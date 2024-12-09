import logging
from itertools import groupby
from typing import List

from web3 import Web3

from common.utils.web3_utils import ZERO_ADDRESS, event_topic_to_address
from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import FilterTransactionDataJob
from indexer.modules.custom.etherfi.abi.event import *
from indexer.modules.custom.etherfi.abi.functions import *
from indexer.modules.custom.etherfi.domains.eeth import (
    EtherFiPositionValuesD,
    EtherFiShareBalanceCurrentD,
    EtherFiShareBalanceD,
)
from indexer.modules.custom.etherfi.domains.lrts import EtherFiLrtExchangeRateD
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper

logger = logging.getLogger(__name__)


class ExportEtherFiShareJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [EtherFiShareBalanceD, EtherFiPositionValuesD, EtherFiShareBalanceCurrentD, EtherFiLrtExchangeRateD]
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

        self.position_events = [
            validator_approved_event.get_signature(),
            validator_registration_canceled_event.get_signature(),
            rebase_event.get_signature(),
        ]

        self._accountants = [a["accountant"].lower() for a in self.user_defined_config.get("lrts", [])]
        self._accountants_to_tokens = {
            a["accountant"].lower(): a["token"] for a in self.user_defined_config.get("lrts", [])
        }

        self.topic_addresses = [
            self.user_defined_config["eeth_address"],
            self.user_defined_config["liquidity_pool_address"],
        ]

        self.multicall_helper = MultiCallHelper(
            self._web3, {"batch_size": kwargs["batch_size"], "multicall": True, "max_workers": kwargs["max_workers"]}
        )

    def get_filter(self):
        return [
            TransactionFilterByLogs(
                [
                    TopicSpecification(
                        addresses=self.topic_addresses + self._accountants,
                        topics=self.position_events
                        + [transfer_share_event.get_signature(), exchange_rate_changed_event.get_signature()],
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
            if log.address.lower() in self._accountants:
                self._collect_exchange_rate(log)
                continue
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

        self._collect_shares(shares_holders)
        self._collect_positions(block_to_update_position)

    def _collect_shares(self, shares_holders):
        share_calls = []
        for block_number, addresses in shares_holders.items():
            for address in addresses:
                if address == ZERO_ADDRESS:
                    continue
                share_call = Call(
                    target=self.user_defined_config["eeth_address"],
                    function_abi=get_shares_func,
                    block_number=block_number,
                    parameters=[address],
                )
                share_calls.append(share_call)

        self.multicall_helper.execute_calls(share_calls)
        shares_current = []
        for call in share_calls:
            self._collect_domain(
                EtherFiShareBalanceD(
                    address=call.parameters[0],
                    token_address=call.target,
                    shares=call.returns["shares"],
                    block_number=call.block_number,
                )
            )
            shares_current.append(
                EtherFiShareBalanceCurrentD(
                    address=call.parameters[0],
                    token_address=call.target,
                    shares=call.returns["shares"],
                    block_number=call.block_number,
                )
            )
        shares_current.sort(key=lambda x: (x.address, x.token_address, x.block_number))
        self._data_buff[EtherFiShareBalanceCurrentD.type()] = [
            list(group)[-1] for key, group in groupby(shares_current, key=lambda x: (x.address, x.token_address))
        ]

    def _collect_positions(self, block_to_update_position):
        position_calls = []
        for block_number in block_to_update_position:
            total_shares_call = Call(
                target=self.user_defined_config["eeth_address"],
                function_abi=total_shares_func,
                block_number=block_number,
            )
            total_value_out_lp_call = Call(
                target=self.user_defined_config["liquidity_pool_address"],
                function_abi=total_value_out_lp_func,
                block_number=block_number,
            )
            total_value_in_lp_call = Call(
                target=self.user_defined_config["liquidity_pool_address"],
                function_abi=total_value_in_lp_func,
                block_number=block_number,
            )
            position_calls.extend([total_shares_call, total_value_out_lp_call, total_value_in_lp_call])

        self.multicall_helper.execute_calls(position_calls)
        position_domains = {}
        for call in position_calls:
            if call.block_number not in position_domains:
                position_domains[call.block_number] = EtherFiPositionValuesD(
                    block_number=call.block_number,
                    total_share=0,
                    total_value_out_lp=0,
                    total_value_in_lp=0,
                )
            if call.data == total_shares_func.get_signature():
                position_domains[call.block_number].total_share = call.returns["totalShares"]
            if call.data == total_value_out_lp_func.get_signature():
                position_domains[call.block_number].total_value_out_lp = call.returns["totalValueOutOfLp"]
            if call.data == total_value_in_lp_func.get_signature():
                position_domains[call.block_number].total_value_in_lp = call.returns["totalValueInLp"]
        for block_number, domain in position_domains.items():
            self._collect_domain(domain)

    def _collect_exchange_rate(self, log: Log):
        if log.topic0 != exchange_rate_changed_event.get_signature():
            return
        log_data = exchange_rate_changed_event.decode_log(log)
        self._collect_domain(
            EtherFiLrtExchangeRateD(
                block_number=log.block_number,
                exchange_rate=log_data["newRate"],
                token_address=self._accountants_to_tokens[log.address.lower()],
            )
        )
