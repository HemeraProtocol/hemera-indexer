import logging
from itertools import groupby
from typing import List

from hemera.common.utils.web3_utils import ZERO_ADDRESS, event_topic_to_address
from hemera.indexer.domains.log import Log
from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.executors.batch_work_executor import BatchWorkExecutor
from hemera.indexer.jobs.base_job import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera_udf.lido.abi.event import *
from hemera_udf.lido.abi.functions import *
from hemera_udf.lido.domains import LidoPositionValuesD, LidoShareBalanceCurrentD, LidoShareBalanceD

logger = logging.getLogger(__name__)


class ExportLidoShareJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [LidoShareBalanceD, LidoShareBalanceCurrentD, LidoPositionValuesD]
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
        self.multicall_helper = MultiCallHelper(
            self._web3, {"batch_size": kwargs["batch_size"], "multicall": True, "max_workers": kwargs["max_workers"]}
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
            if log.address.lower() != self.user_defined_config["seth_address"]:
                continue
            if log.topic0 == transfer_share_event.get_signature():
                from_address = event_topic_to_address(log.topic1)
                to_address = event_topic_to_address(log.topic2)
                if from_address == ZERO_ADDRESS or to_address == ZERO_ADDRESS:
                    block_to_update_position.add(log.block_number)
                    continue
                shares_holder.setdefault(log.block_number, set()).add(from_address)
                shares_holder.setdefault(log.block_number, set()).add(to_address)
            if log.topic0 in self.position_events:
                block_to_update_position.add(log.block_number)

        self._collect_shares(shares_holder)
        self._collect_positions(block_to_update_position)

    def _collect_shares(self, shares_holder):
        share_calls = []
        for block_number, addresses in shares_holder.items():
            for address in addresses:
                if address == ZERO_ADDRESS:
                    continue
                share_call = Call(
                    target=self.user_defined_config["seth_address"],
                    function_abi=get_shares_func,
                    block_number=block_number,
                    parameters=[address],
                )
                share_calls.append(share_call)

        self.multicall_helper.execute_calls(share_calls)
        shares_current = []
        for call in share_calls:
            self._collect_domain(
                LidoShareBalanceD(
                    address=call.parameters[0],
                    token_address=call.target,
                    shares=call.returns["shares"],
                    block_number=call.block_number,
                )
            )
            shares_current.append(
                LidoShareBalanceCurrentD(
                    address=call.parameters[0],
                    token_address=call.target,
                    shares=call.returns["shares"],
                    block_number=call.block_number,
                )
            )
        shares_current.sort(key=lambda x: (x.address, x.token_address, x.block_number))
        self._data_buff[LidoShareBalanceCurrentD.type()] = [
            list(group)[-1] for key, group in groupby(shares_current, key=lambda x: (x.address, x.token_address))
        ]

    def _collect_positions(self, block_to_update_position):
        position_calls = []
        for block_number in block_to_update_position:
            total_shares_call = Call(
                target=self.user_defined_config["seth_address"],
                function_abi=get_total_shares_func,
                block_number=block_number,
            )
            buffered_ether_call = Call(
                target=self.user_defined_config["seth_address"],
                function_abi=get_buffered_ether_func,
                block_number=block_number,
            )
            deposited_validators_call = Call(
                target=self.user_defined_config["seth_address"],
                function_abi=get_beacon_stat_func,
                block_number=block_number,
            )
            position_calls.extend([total_shares_call, buffered_ether_call, deposited_validators_call])

        self.multicall_helper.execute_calls(position_calls)
        position_domains = {}
        for call in position_calls:
            if call.block_number not in position_domains:
                position_domains[call.block_number] = LidoPositionValuesD(
                    block_number=call.block_number,
                    total_share=0,
                    buffered_eth=0,
                    consensus_layer=0,
                    deposited_validators=0,
                    cl_validators=0,
                )
            if call.data == get_total_shares_func.get_signature():
                position_domains[call.block_number].total_share = call.returns["totalShares"]
            if call.data == get_buffered_ether_func.get_signature():
                position_domains[call.block_number].buffered_eth = call.returns["bufferedEther"]
            if call.data == get_beacon_stat_func.get_signature():
                position_domains[call.block_number].deposited_validators = call.returns["depositedValidators"]
                position_domains[call.block_number].cl_validators = call.returns["beaconValidators"]
                position_domains[call.block_number].consensus_layer = call.returns["beaconBalance"]
        for block_number, domain in position_domains.items():
            self._collect_domain(domain)
