import logging
from typing import List

from web3 import Web3

from common.utils.web3_utils import ZERO_ADDRESS, event_topic_to_address
from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.etherfi.abi.contract import eeth_abi, liquidity_pool_abi
from indexer.modules.custom.etherfi.abi.event import *
from indexer.modules.custom.etherfi.domains.eeth import EtherFiPositionValues, EtherFiShareBalance
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportEtherFiShareJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [EtherFiShareBalance, EtherFiPositionValues]
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
        self.eeth_contract = self._web3.eth.contract(
            address=Web3.to_checksum_address(self.user_defined_config["eeth_address"]), abi=eeth_abi
        )
        self.liquidity_pool_contract = self._web3.eth.contract(
            address=Web3.to_checksum_address(self.user_defined_config["liquidity_pool_address"]), abi=liquidity_pool_abi
        )

        self.position_events = [
            validator_approved_event.get_signature(),
            validator_registration_canceled_event.get_signature(),
            rebase_event.get_signature(),
        ]

        self.topic_addresses = [
            self.user_defined_config["eeth_address"],
            self.user_defined_config["liquidity_pool_address"],
        ]

    def get_filter(self):
        return [
            TransactionFilterByLogs(
                [
                    TopicSpecification(
                        addresses=self.topic_addresses,
                        topics=self.position_events + [transfer_share_event.get_signature()],
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
        # block_number -> address set
        shares_holders = {}

        block_to_update_position = set()

        for log in logs:
            if log.address not in self.topic_addresses:
                continue
            if log.topic0 == transfer_share_event.get_signature():
                from_address = event_topic_to_address(log.topic1)
                to_address = event_topic_to_address(log.topic2)
                if from_address == ZERO_ADDRESS or to_address == ZERO_ADDRESS:
                    block_to_update_position.add(log.block_number)

                shares_holders.setdefault(log.block_number, set()).add(from_address)
                shares_holders.setdefault(log.block_number, set()).add(to_address)
            if log.topic0 in self.position_events:
                block_to_update_position.add(log.block_number)

        for block_number, addresses in shares_holders.items():
            for address in addresses:
                if address == ZERO_ADDRESS:
                    continue
                shares = self.eeth_contract.functions.shares(address).call(block_identifier=block_number)
                share_domain = EtherFiShareBalance(
                    address=address,
                    token_address=self.user_defined_config["eeth_address"],
                    shares=shares,
                    block_number=block_number,
                )
            self._collect_domain(share_domain)

        for block_number in block_to_update_position:
            total_shares = self.eeth_contract.functions.totalShares().call(block_identifier=block_number)
            total_value_out_lp = self.liquidity_pool_contract.functions.totalValueOutOfLp().call(
                block_identifier=block_number
            )
            total_value_in_lp = self.liquidity_pool_contract.functions.totalValueInLp().call(
                block_identifier=block_number
            )
            self._collect_domain(
                EtherFiPositionValues(
                    block_number=block_number,
                    total_share=total_shares,
                    total_value_out_lp=total_value_out_lp,
                    total_value_in_lp=total_value_in_lp,
                )
            )
