import json
import logging
from dataclasses import dataclass
from typing import List

import requests
from eth_account import Account
from eth_typing import BlockNumber
from web3 import Web3

from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from common.utils.web3_utils import get_account_from_file
from indexer.domain.block import Block
from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.avs_operator.abi.contract import RegistryCoordinatorABI
from indexer.modules.custom.avs_operator.abi.event import IndexRecordEvent
from indexer.modules.custom.avs_operator.aggregator.client import AggregatorClient
from indexer.modules.custom.avs_operator.aggregator.task import AlertTaskInfo
from indexer.modules.custom.avs_operator.bn128.sign import sign_message
from indexer.modules.custom.avs_operator.domains.domain import HemeraHistoryTransparency, LogWithDecodeData
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ValidateAndAggregate(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [HemeraHistoryTransparency]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._filters = kwargs.get("filters", [])
        self.index_record_event = IndexRecordEvent()
        # TODO: replace by dataclass.get_code_hash()
        self.block_dataclass = hex_str_to_bytes("0x67a70c90")
        self.tx_dataclass = hex_str_to_bytes("0x6048a7e2")

        self.operator_ecdsa_private_key = get_account_from_file(self.user_defined_config["operator_ecdsa_key_file"], self.user_defined_config["operator_ecdsa_password_file"])
        self.operator_bls_private_key = get_account_from_file(self.user_defined_config["operator_bls_key_file"], self.user_defined_config["operator_bls_password_file"])
        self.operator_bls_private_key = int.from_bytes(self.operator_bls_private_key, "big")
        self.registry_coordinator_contract = self._web3.eth.contract(
            address=self.user_defined_config["avs_registry_coordinator_address"], abi=RegistryCoordinatorABI
        )
        self.aggregator_client = AggregatorClient(self.user_defined_config["aggregator_host"])

        if not self._check_operator_is_registered():
            logger.error("Operator is not registered. Exiting the program.")
            raise SystemError(
                "operator is not registered. Registering operator using the operator-cli before starting operator"
            )
        self.operator_id = self._get_operator_id()
        self.verify_rpc_client = Web3(Web3.HTTPProvider(self.user_defined_config["verify_rpc"]))

    def _check_operator_is_registered(self) -> bool:
        status = self.registry_coordinator_contract.functions.getOperatorStatus(
            self.operator_ecdsa_private_key.address
        ).call()
        return status == 1

    def _get_operator_id(self) -> bytes:
        operator_id = self.registry_coordinator_contract.functions.getOperatorId(
            self.operator_ecdsa_private_key.address
        ).call()
        return bytes_to_hex_str(operator_id)

    def get_filter(self):
        return [
            TransactionFilterByLogs(
                [
                    TopicSpecification(
                        addresses=[self.user_defined_config["history_transparency_address"]],
                        topics=[self.index_record_event.get_signature()],
                    )
                ]
            ),
        ]

    def _collect(self, **kwargs):
        pass

    def _process(self, **kwargs):
        logs: List[Log] = self._data_buff.get(Log.type(), [])

        verified_logs = self._verify_logs(logs)
        for log in verified_logs:
            item = self._confirm_task(log)
            self._collect_item(item.type(), item)

    def _verify_logs(self, logs: List[Log]):
        block_log = []
        tx_log = []
        block_nums = set()
        block_data = {}
        for log in logs:
            if log.topic0.lower() != self.index_record_event.get_signature().lower():
                continue
            decode_data = self.index_record_event.decode_log(log)
            if decode_data["outputs"]["dataClass"] == self.block_dataclass:
                block_log.append(LogWithDecodeData(log, decode_data, False))
                block_nums |= set(range(decode_data["startBlock"], decode_data["endBlock"] + 1))
            elif decode_data["outputs"]["dataClass"] == self.tx_dataclass:
                tx_log.append(LogWithDecodeData(log, decode_data, False))
                block_nums |= set(range(decode_data["startBlock"], decode_data["endBlock"] + 1))

        # request block data from api
        for block_num in block_nums:
            api_block = self._get_block_api(block_num)
            if not api_block:
                continue
            rpc_block = self._get_block_rpc(block_num)
            if rpc_block is None:
                continue
            if not self._compare_block(rpc_block, api_block):
                continue

            block_data[block_num] = api_block

        for log in block_log:
            count = 0
            for block_num in range(log.decode_data["startBlock"], log.decode_data["endBlock"] + 1):
                if block_num in block_data:
                    count += 1
            if count == log.decode_data["outputs"]["count"]:
                log.verified = True

        for log in tx_log:
            count = 0
            for block_num in range(log.decode_data["startBlock"], log.decode_data["endBlock"] + 1):
                api_block = block_data.get(block_num)
                if api_block is not None:
                    count += api_block["transactions_count"]
            if count == log.decode_data["outputs"]["count"]:
                log.verified = True

        return block_log + tx_log

    def _get_block_api(self, block_num):
        try:
            res = requests.get(f"{self.user_defined_config['verify_api']}{block_num}")
            if res.status_code != 200:
                raise ValueError(f"Failed to get block data for {block_num}: {res.status_code}")
            api_block = res.json()
            return api_block
        except Exception as e:
            logger.error(f"Failed to get block data for {block_num}: {e}")
            return None

    def _get_block_rpc(self, block_num):
        try:
            return self.verify_rpc_client.eth.get_block(block_num, full_transactions=True)
        except Exception as e:
            logger.error(f"Failed to get block data for {block_num}: {e}")
            return None

    def _compare_block(self, rpc_block, api_block) -> bool:
        if rpc_block.hash.hex() != api_block["hash"]:
            logger.error(f"Block hash mismatch for {rpc_block.number}")
            return False
        if len(rpc_block["transactions"]) != api_block["transactions_count"]:
            logger.error(f"Transactions count mismatch for {rpc_block.number}")
            return False
        rpc_txs = sorted(rpc_block.transactions, key=lambda x: x["transactionIndex"])
        api_txs = sorted(api_block["transactions"], key=lambda x: x["transaction_index"])
        for i in range(len(rpc_txs)):
            if rpc_txs[i]["hash"].hex() != api_txs[i]["hash"]:
                logger.error(f"Transaction hash mismatch for {rpc_block.number}, index {i}")
                return False
        return True

    def _confirm_task(self, log: LogWithDecodeData) -> HemeraHistoryTransparency:
        decode_data = log.decode_data

        hs = HemeraHistoryTransparency(
            start_block=decode_data["startBlock"],
            end_block=decode_data["endBlock"],
            code_hash=decode_data["codeHash_"],
            data_class=decode_data["outputs"]["dataClass"],
            data_hash=decode_data["outputs"]["dataHash"],
            msg_hash=None,
            count=decode_data["outputs"]["count"],
            verify_status=log.verified,
            confirm_status=False,
        )
        hs.msg_hash = hs.message_hash()

        if log.verified is False:
            return hs

        try:
            task_resp: AlertTaskInfo = self.aggregator_client.create_alert_task(bytes_to_hex_str(hs.msg_hash))
        except ValueError as e:
            logger.error(f"Failed to create alert task for {hs}: {e}")
            return hs
        bls_hash = sign_message(self.operator_bls_private_key, task_resp.sign_hash())
        try:
            self.aggregator_client.send_signed_task_response(task_resp, bls_hash, self.operator_id)
            hs.confirm_status = True
        except Exception as e:
            logger.error(f"Failed to send signed task response for {hs}: {e}")
        return hs
