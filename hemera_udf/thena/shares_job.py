import logging

from hemera.indexer.domains.token_transfer import ERC20TokenTransfer
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera_udf.thena.abi import BALANCE_OF_FUNCTION, BASE_LOWER_FUNCTION, BASE_UPPER_FUNCTION, TOTAL_SUPPLY_FUNCTION
from hemera_udf.thena.domains.feature_thena import ThenaSharesDomain

logger = logging.getLogger(__name__)


class ThenaSharesJob(FilterTransactionDataJob):
    dependency_types = [ERC20TokenTransfer]
    output_types = [ThenaSharesDomain]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = kwargs["config"].get("db_service")
        config = kwargs["config"]["thena_job"]
        self.gamma_pool_address = config["gamma_pool_address"]
        self.thena_farming_pool_address = config["thena_farming_pool_address"]
        self.thena_liquidity_pool = config.get("thena_liquidity_pool_address")

        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    addresses=[self.gamma_pool_address],
                ),
            ]
        )

    def _process(self, **kwargs):
        erc20_token_transfers = self._data_buff[ERC20TokenTransfer.type()]
        wallet_address_dict = {}
        for tt in erc20_token_transfers:
            if tt.token_address == self.gamma_pool_address:
                common_data = {
                    "target": self.thena_farming_pool_address,
                    "block_number": tt.block_number,
                    "user_defined_k": tt.block_timestamp,
                }
                wallet_address_dict[tt.from_address, tt.block_number] = {**common_data, "parameters": [tt.from_address]}
                wallet_address_dict[tt.to_address, tt.block_number] = {**common_data, "parameters": [tt.to_address]}

        # share
        call_dict_list = list(wallet_address_dict.values())
        shares_list = []

        for call_dict in call_dict_list:
            call = Call(**call_dict, function_abi=BALANCE_OF_FUNCTION)
            shares_list.append(call)

        self.multi_call_helper.execute_calls(shares_list)

        # total supply
        supply_list = []
        tick_lower_list = []
        tick_upper_list = []

        for call_dict in call_dict_list:
            call_dict.pop("parameters")
            call = Call(**call_dict, function_abi=TOTAL_SUPPLY_FUNCTION)
            supply_list.append(call)

            call_dict_copy = call_dict.copy()
            call_dict_copy["target"] = self.gamma_pool_address

            call = Call(**call_dict_copy, function_abi=BASE_LOWER_FUNCTION)
            tick_lower_list.append(call)

            call = Call(**call_dict_copy, function_abi=BASE_UPPER_FUNCTION)
            tick_upper_list.append(call)

        self.multi_call_helper.execute_calls(supply_list)
        self.multi_call_helper.execute_calls(tick_lower_list)
        self.multi_call_helper.execute_calls(tick_upper_list)

        for shares_call, supply_call, tick_lower_call, tick_upper_call in zip(
            shares_list, supply_list, tick_lower_list, tick_upper_list
        ):
            if shares_call.returns:
                shares = shares_call.returns.get("")
                total_supply = supply_call.returns.get("")
                tick_lower = tick_lower_call.returns.get("")
                tick_upper = tick_upper_call.returns.get("")

                shares_domain = ThenaSharesDomain(
                    farming_address=self.thena_farming_pool_address,
                    gamma_address=self.gamma_pool_address,
                    pool_address=self.thena_liquidity_pool,
                    wallet_address=shares_call.parameters[0],
                    total_supply=total_supply,
                    shares=shares,
                    tick_lower=tick_lower,
                    tick_upper=tick_upper,
                    block_number=shares_call.block_number,
                    block_timestamp=shares_call.user_defined_k,
                )
                self._collect_domain(shares_domain)
