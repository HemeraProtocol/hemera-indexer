import json
import logging
from typing import List

from common.utils.abi_code_utils import decode_data, encode_data
from common.utils.exception_control import HemeraBaseException
from enumeration.record_level import RecordLevel
from indexer.domain.block import Block
from indexer.domain.contract import Contract, extract_contract_from_trace
from indexer.domain.trace import Trace
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import BaseExportJob
from indexer.utils.abi_setting import TOKEN_NAME_FUNCTION
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.rpc_utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
exception_recorder = ExceptionRecorder()


# Exports contracts
class ExportContractsJob(BaseExportJob):
    dependency_types = [Block, Trace]
    output_types = [Contract]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1

    def _collect(self, **kwargs):
        contracts = build_contracts(self._data_buff[Trace.type()])

        self._batch_work_executor.execute(contracts, self._collect_batch, total_items=len(contracts))
        self._batch_work_executor.wait()

    def _collect_batch(self, contracts):
        contracts = contract_info_rpc_requests(self._batch_web3_provider.make_request, contracts, self._is_batch)

        for contract in contracts:
            self._collect_item(Contract.type(), Contract(contract))

    def _process(self, **kwargs):
        transaction_mapping = {
            transaction.hash: transaction.from_address
            for transaction in [
                transaction for block in self._data_buff[Block.type()] for transaction in block.transactions
            ]
        }
        for contract in self._data_buff[Contract.type()]:
            contract.fill_transaction_from_address(transaction_mapping[contract.transaction_hash])

        self._data_buff[Contract.type()].sort(key=lambda x: (x.block_number, x.transaction_index, x.address))


def build_contracts(traces: List[Trace]):
    contracts = []
    for trace in traces:
        if (
            trace.trace_type in ["create", "create2"]
            and trace.to_address is not None
            and len(trace.to_address) > 0
            and trace.status == 1
        ):
            contract = extract_contract_from_trace(trace)
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
