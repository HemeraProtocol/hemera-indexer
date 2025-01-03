#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/1/3 14:11
# @Author  ideal93
# @File  export_contracts_from_transaction_job.py
# @Brief

import json
import logging
from typing import List, Optional, Union

from hemera.common.enumeration.record_level import RecordLevel
from hemera.common.utils.abi_code_utils import decode_data, encode_data
from hemera.common.utils.exception_control import HemeraBaseException
from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.indexer.domains.contract import Contract, ContractFromTransaction, extract_contract_from_transaction
from hemera.indexer.domains.trace import Trace
from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.executors.batch_work_executor import BatchWorkExecutor
from hemera.indexer.jobs.base_job import BaseExportJob
from hemera.indexer.utils.abi_setting import TOKEN_NAME_FUNCTION
from hemera.indexer.utils.exception_recorder import ExceptionRecorder
from hemera.indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from hemera.indexer.utils.rpc_utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
exception_recorder = ExceptionRecorder()


# Exports contracts
class ExportContractsFromTransactionJob(BaseExportJob):
    dependency_types = [Transaction]
    output_types = [ContractFromTransaction]
    able_to_reorg = True

    def get_code(self, address, block_number: Union[str, int, None]) -> Optional[str]:
        if block_number is not None:
            if isinstance(block_number, int):
                block_number = hex(block_number)
        else:
            block_number = "latest"
        try:
            address = self._web3.to_checksum_address(address)
            code = self._web3.eth.get_code(address, block_number)
            return code.hex()
        except Exception as e:
            return None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1

    def _collect(self, **kwargs):
        contracts = self.build_contracts(self._data_buff[Transaction.type()])

        self._batch_work_executor.execute(contracts, self._collect_batch, total_items=len(contracts))
        self._batch_work_executor.wait()

    def _collect_batch(self, contracts):
        contracts = contract_info_rpc_requests(self._batch_web3_provider.make_request, contracts, self._is_batch)

        for contract in contracts:
            self._collect_item(ContractFromTransaction.type(), ContractFromTransaction(contract))

    def _process(self, **kwargs):
        self._data_buff[ContractFromTransaction.type()].sort(
            key=lambda x: (x.block_number, x.transaction_index, x.address)
        )

    def build_contracts(self, transactions: List[Transaction]):
        contracts = []
        for transaction in transactions:
            if transaction.receipt.contract_address is not None and transaction.receipt.status == 1:
                contract = extract_contract_from_transaction(transaction)
                contract["deployed_code"] = self.get_code(contract["address"], transaction.block_number)

                contract["param_to"] = contract["address"]

                try:
                    contract["param_data"] = encode_data(
                        TOKEN_NAME_FUNCTION.get_abi(), [], TOKEN_NAME_FUNCTION.get_signature()
                    )
                except Exception as e:
                    logger.warning(
                        f"Encoding contract api parameter failed. "
                        f"contract address: {contract['address']}. "
                        f"fn: name. "
                        f"exception: {e}. "
                    )
                    contract["param_data"] = "0x"

                contract["param_number"] = hex(contract["block_number"])
                contracts.append(contract)

        return contracts


def contract_info_rpc_requests(make_requests, contracts, is_batch):
    for idx, contract in enumerate(contracts):
        contract["request_id"] = idx

    contract_name_rpc = list(generate_eth_call_json_rpc(contracts))

    if is_batch:
        response = make_requests(params=json.dumps(contract_name_rpc))
    else:
        response = [make_requests(params=json.dumps(contract_name_rpc[0]))]

    for data in list(zip_rpc_response(contracts, response)):
        contract = data[0]
        try:
            result = rpc_response_to_result(data[1])
        except HemeraBaseException as e:
            result = None
            logger.warning(
                f"eth call contract name failed. "
                f"contract address: {contract['address']}. "
                f"rpc response: {result}. "
                f"exception: {e}"
            )
            exception_recorder.log(
                block_number=data[0]["block_number"],
                dataclass=Contract.type(),
                message_type=e.__class__.__name__,
                message=str(e),
                exception_env=data[1],
                level=RecordLevel.WARN,
            )

        info = result[2:] if result is not None else None

        try:
            contract["name"] = decode_data(["string"], bytes.fromhex(info))[0].replace("\u0000", "")
        except Exception as e:
            logger.warning(
                f"Decoding contract name failed. "
                f"contract address: {contract['address']}. "
                f"rpc response: {result}. "
                f"exception: {e}"
            )
            exception_recorder.log(
                block_number=data[0]["block_number"],
                dataclass=Contract.type(),
                message_type="DecodeNameFail",
                message=str(e),
                exception_env=contract,
                level=RecordLevel.WARN,
            )
            contract["name"] = None

    return contracts
