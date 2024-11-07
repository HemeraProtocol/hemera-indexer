import logging
from typing import List

from web3 import Web3

from common.utils.web3_utils import ZERO_ADDRESS, event_topic_to_address
from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.lido.abi.contract import seth_abi
from indexer.modules.custom.lido.abi.event import *
from indexer.modules.custom.lido.domains.seth import LidoPositionValues, LidoShareBalance
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportLidoShareJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [LidoShareBalance, LidoPositionValues]
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

        self.position_events = [
            shares_burnt_event.get_signature(),
            submitted_event.get_signature(),
            el_rewards_received_event.get_signature(),
            withdrawals_received_event.get_signature(),
            unbuffered_event.get_signature(),
            eth_distributed_event.get_signature(),
            cl_validators_updated_event.get_signature(),
            deposited_validators_changed_event.get_signature(),
        ]

    def get_filter(self):
        return [
            TransactionFilterByLogs(
                [
                    TopicSpecification(
                        addresses=[
                            self.user_defined_config["seth_address"],
                        ],
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
        shares_holder = {}
        block_to_update_position = set()

        for log in logs:
            if log.topic0 == transfer_share_event.get_signature():
                from_address = event_topic_to_address(log.topic1)
                to_address = event_topic_to_address(log.topic2)
                if from_address == ZERO_ADDRESS or to_address == ZERO_ADDRESS:
                    continue
                shares_holder.setdefault(log.block_number, set()).add(from_address)
                shares_holder.setdefault(log.block_number, set()).add(to_address)
            if log.topic0 in self.position_events:
                block_to_update_position.add(log.block_number)

        for block_number, addresses in shares_holder.items():
            for address in addresses:
                if address == ZERO_ADDRESS:
                    continue
                balance = self.seth_contract.functions.balanceOf(address).call(block_identifier=block_number)
                share_balance = self.seth_contract.functions.getSharesByPooledEth(balance).call(
                    block_identifier=block_number
                )
                share_domain = LidoShareBalance(
                    address=address,
                    token_address=log.address,
                    balance=share_balance,
                    block_number=block_number,
                )
                self._collect_domain(share_domain)

        for block_number in block_to_update_position:
            total_shares = self.seth_contract.functions.getTotalShares().call(block_identifier=block_number)
            buffered_ether = self.seth_contract.functions.getBufferedEther().call(block_identifier=block_number)
            deposited_validators, cl_validators, cl_balance = self.seth_contract.functions.getBeaconStat().call(
                block_identifier=block_number
            )
            self._collect_domain(
                LidoPositionValues(
                    block_number=block_number,
                    total_share=total_shares,
                    buffered_eth=buffered_ether,
                    deposited_validators=deposited_validators,
                    consensus_layer=cl_balance,
                    cl_validators=cl_validators,
                )
            )
