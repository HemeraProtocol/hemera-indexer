import logging
from typing import List

from web3 import Web3

from common.utils.web3_utils import ZERO_ADDRESS, event_topic_to_address
from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.lido.abi.contract import seth_abi
from indexer.modules.custom.lido.abi.event import transfer_share_event
from indexer.modules.custom.lido.domains.seth import LidoPositionBalance, LidoShareBalance
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportLidoShareJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [LidoShareBalance, LidoPositionBalance]
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
        self.seth_contract = self._web3.eth.contract(
            address=Web3.to_checksum_address(self.user_defined_config["seth_address"]), abi=seth_abi
        )

    def get_filter(self):
        return [
            TransactionFilterByLogs(
                [
                    TopicSpecification(
                        addresses=[
                            self.user_defined_config["seth_address"],
                        ],
                        topics=[transfer_share_event.get_signature()],
                    )
                ]
            ),
        ]

    def _collect(self, **kwargs):
        pass

    def _process(self, **kwargs):
        logs: List[Log] = self._data_buff.get(Log.type(), [])
        if len(logs) == 0:
            return
        sharesHolder = set()
        for log in logs:
            if log.topic0 == transfer_share_event.get_signature():
                sharesHolder.add(event_topic_to_address(log.topic1))
                sharesHolder.add(event_topic_to_address(log.topic2))
        last_block_number = logs[-1].block_number

        for address in sharesHolder:
            if address == ZERO_ADDRESS:
                continue
            balance = self.seth_contract.functions.balanceOf(address).call(block_identifier=last_block_number)
            share_balance = self.seth_contract.functions.getSharesByPooledEth(balance).call(
                block_identifier=last_block_number
            )
            share_domain = LidoShareBalance(
                address=address,
                token_address=log.address,
                balance=share_balance,
                block_number=last_block_number,
                block_timestamp=logs[-1].block_timestamp,
            )
            self._collect_domain(share_domain)
