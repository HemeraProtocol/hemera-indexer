import logging
from itertools import groupby
from typing import List

from hemera.common.utils.web3_utils import ZERO_ADDRESS, event_topic_to_address
from hemera.indexer.domains.log import Log
from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.executors.batch_work_executor import BatchWorkExecutor
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.abi_setting import ERC20_BALANCE_OF_FUNCTION, ERC20_TRANSFER_EVENT
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera_udf.pendle.abi.event import redeem_rewards_event
from hemera_udf.pendle.abi.function import *
from hemera_udf.pendle.domains.market import PendleUserActiveBalanceCurrentD, PendleUserActiveBalanceD
from hemera_udf.pendle.models.market import PendlePool

logger = logging.getLogger(__name__)


class PendleTokenBalanceJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [PendleUserActiveBalanceD, PendleUserActiveBalanceCurrentD]
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
        self._get_all_market(kwargs["config"].get("db_service"))

    def _get_all_market(self, db_service):
        markets = db_service.get_service_session().query(PendlePool).all()
        self._all_markets = [m.market_address.lower() for m in markets]
        self._all_markets_map = {m.market_address.lower(): m for m in markets}

    def get_filter(self):
        return [
            TransactionFilterByLogs(
                [
                    TopicSpecification(
                        addresses=self._all_markets,
                        topics=[ERC20_TRANSFER_EVENT.get_signature(), redeem_rewards_event.get_signature()],
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

        to_requests = set()
        for log in logs:
            if log.address.lower() not in self._all_markets:
                continue
            if log.topic0 == ERC20_TRANSFER_EVENT.get_signature():
                to_requests.add((log.address, event_topic_to_address(log.topic1), log.block_number))
                to_requests.add((log.address, event_topic_to_address(log.topic2), log.block_number))
            elif log.topic0 == redeem_rewards_event.get_signature():
                to_requests.add((log.address, event_topic_to_address(log.topic1), log.block_number))
        if len(to_requests) == 0:
            return

        calls = []
        domain_data = []
        call_to_domain_data = {}
        for market_address, user_address, block_number in to_requests:
            if user_address == ZERO_ADDRESS:
                continue
            market = self._all_markets_map.get(market_address.lower())
            if not market:
                continue

            call_id_prefix = f"{market_address}-{user_address}-{block_number}"
            domain = PendleUserActiveBalanceD(
                market_address=market_address,
                user_address=user_address,
                block_number=block_number,
                chain_id=self._chain_id,
                sy_balance=0,
                active_balance=0,
                total_active_supply=0,
                market_sy_balance=0,
            )
            domain_data.append(domain)

            # sy balance
            c = Call(
                target=market.sy_address,
                function_abi=ERC20_BALANCE_OF_FUNCTION,
                parameters=[user_address],
                block_number=block_number,
            )
            call_to_domain_data[id(c)] = domain
            calls.append(c)
            # user active balance
            c = Call(
                target=market_address,
                function_abi=market_active_balance,
                parameters=[user_address],
                block_number=block_number,
            )
            call_to_domain_data[id(c)] = domain
            calls.append(c)

            # market totalActiveSupply
            c = Call(
                target=market_address,
                function_abi=market_total_active_supply,
                parameters=[],
                block_number=block_number,
            )
            call_to_domain_data[id(c)] = domain
            calls.append(c)

            # market sy balance
            c = Call(
                target=market.sy_address,
                function_abi=ERC20_BALANCE_OF_FUNCTION,
                parameters=[market_address],
                block_number=block_number,
            )
            call_to_domain_data[id(c)] = domain
            calls.append(c)

        self.multicall_helper.execute_calls(calls)

        for call in calls:
            domain = call_to_domain_data[id(call)]
            if "total" in call.returns:
                domain.total_active_supply = call.returns["total"]
                continue
            if "active_balance" in call.returns:
                domain.active_balance = call.returns["active_balance"]
                continue
            if "balance" in call.returns:
                if call.parameters[0] in self._all_markets:
                    domain.market_sy_balance = call.returns["balance"]
                else:
                    domain.sy_balance = call.returns["balance"]

        current_domains = [
            PendleUserActiveBalanceCurrentD(
                market_address=d.market_address,
                user_address=d.user_address,
                sy_balance=d.sy_balance,
                active_balance=d.active_balance,
                total_active_supply=d.total_active_supply,
                market_sy_balance=d.market_sy_balance,
                block_number=d.block_number,
                chain_id=d.chain_id,
            )
            for d in domain_data
        ]
        current_domains.sort(key=lambda x: (x.market_address, x.user_address, x.block_number))
        self._data_buff[PendleUserActiveBalanceCurrentD.type()] = [
            list(group)[-1] for key, group in groupby(current_domains, key=lambda x: (x.market_address, x.user_address))
        ]

        self._collect_items(PendleUserActiveBalanceD.type(), domain_data)
