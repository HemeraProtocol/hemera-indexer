import logging
from collections import defaultdict

from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.uniswap_v3.domains.feature_uniswap_v3 import (
    IzumiPool,
    IzumiPoolCurrentPrice,
    IzumiPoolPrice,
    IzumiSwapEvent,
)
from indexer.modules.custom.uniswap_v3.izumi_abi import (
    BURN_EVENT,
    DECREASE_LIQUIDITY_EVENT,
    FACTORY_FUNCTION,
    GET_POOL_ID_FUNCTION,
    INCREASE_LIQUIDITY_EVENT,
    MINT_EVENT,
    POINT_DELTA_FUNCTION,
    POOL_CREATED_EVENT,
    SLOT0_FUNCTION,
    SWAP_EVENT,
    TOKEN0_FUNCTION,
    TOKEN1_FUNCTION,
    UPDATE_LIQUIDITY_EVENT,
)
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper

logger = logging.getLogger(__name__)


class ExportIzumiPoolJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [IzumiPool, IzumiPoolPrice, IzumiPoolCurrentPrice, IzumiSwapEvent]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._service = kwargs["config"].get("db_service")
        self._multicall_helper = MultiCallHelper(
            self._web3, {"batch_size": kwargs["batch_size"], "multicall": True, "max_workers": kwargs["max_workers"]}
        )

        config = kwargs["config"]["izumi_pool_job"]
        self._position_token_address = config.get("position_token_address").lower()
        self._factory_address = config.get("factory_address").lower()

        self._exist_pools = get_exist_pools(self._service, self._position_token_address)

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    topics=[
                        # lp change event
                        INCREASE_LIQUIDITY_EVENT.get_signature(),
                        UPDATE_LIQUIDITY_EVENT.get_signature(),
                        DECREASE_LIQUIDITY_EVENT.get_signature(),
                        # position_token_address change event
                        MINT_EVENT.get_signature(),
                        BURN_EVENT.get_signature(),
                        # POOL EVENT
                        POOL_CREATED_EVENT.get_signature(),
                        SWAP_EVENT.get_signature(),
                    ]
                ),
            ]
        )

    def _collect(self, **kwargs):
        transactions = self._data_buff[Transaction.type()]
        logs = self._data_buff[Log.type()]

        # collect pool by create event
        self.get_pools(logs)

        # collect swap event
        self.get_swap_event(transactions, logs)

        # get prices
        self.get_pool_price(logs)

    def get_pools(self, logs):
        maybe_unknown_event_in_swap_eventy_dict = defaultdict(dict)

        new_pool_list = []
        for log in logs:
            log_address = log.address
            if log_address not in self._exist_pools:
                # collect pools by create event
                if log_address == self._factory_address and log.topic0 == POOL_CREATED_EVENT.get_signature():
                    decoded_data = POOL_CREATED_EVENT.decode_log(log)
                    pool_address = decoded_data["pool"]
                    new_pool_dict = {
                        "position_token_address": self._position_token_address,
                        "token0_address": decoded_data["tokenX"],
                        "token1_address": decoded_data["tokenY"],
                        "fee": decoded_data["fee"],
                        "point_delta": decoded_data["pointDelta"],
                        "pool_address": pool_address,
                        "block_number": log.block_number,
                    }
                    self._exist_pools[log_address] = new_pool_dict

                    uniswap_v3_pool = IzumiPool(
                        block_timestamp=log.block_timestamp,
                        factory_address=self._factory_address,
                        pool_id=None,
                        **new_pool_dict,
                    )

                    new_pool_list.append(uniswap_v3_pool)
                # collect pools by swap event
                elif log.topic0 == SWAP_EVENT.get_signature():
                    # if the address created by factory_address ,collect it
                    maybe_unknown_event_in_swap_eventy_dict[log_address] = {
                        "address": log_address,
                        "block_number": log.block_number,
                        "block_timestamp": log.block_timestamp,
                    }

        pools_get_from_swap_event = collect_swap_new_pools(
            self._position_token_address,
            self._factory_address,
            list(maybe_unknown_event_in_swap_eventy_dict.values()),
            self._multicall_helper,
        )
        for pool_address, pool_dict in pools_get_from_swap_event.items():
            if pool_address not in self._exist_pools:
                self._exist_pools[pool_address] = pool_dict
                uniswap_v3_pool = IzumiPool(factory_address=self._factory_address, fee=0, pool_id=None, **pool_dict)

                new_pool_list.append(uniswap_v3_pool)

        # Add pool id to pool list
        pool_id_calls = []
        for pool in new_pool_list:
            pool_id_calls.append(
                Call(
                    target=self._position_token_address,
                    function_abi=GET_POOL_ID_FUNCTION,
                    parameters=[pool.pool_address],
                    block_number=pool.block_number,
                )
            )

        if len(pool_id_calls) > 0:
            self._multicall_helper.execute_calls(pool_id_calls)

            pool_id_mapping = {}
            for call in pool_id_calls:
                pool_address = call.parameters[0]
                pool_id = call.returns["poolId"]
                pool_id_mapping[pool_address] = pool_id

            for pool in new_pool_list:
                pool.pool_id = pool_id_mapping[pool.pool_address]

            self._collect_domains(new_pool_list)

    def get_swap_event(self, transactions, logs):
        _transaction_hash_from_dict = {}
        for transaction in transactions:
            _transaction_hash_from_dict[transaction.hash] = transaction.from_address

        for log in logs:
            if log.address not in self._exist_pools:
                continue
            # Collect swap logs
            if log.topic0 == SWAP_EVENT.get_signature():
                transaction_hash = log.transaction_hash
                decoded_data = SWAP_EVENT.decode_log(log)

                amount0 = decoded_data["amountX"]
                amount1 = decoded_data["amountY"]
                current_point = decoded_data["currentPoint"]
                pool_data = self._exist_pools[log.address]
                self._collect_item(
                    IzumiSwapEvent.type(),
                    IzumiSwapEvent(
                        pool_address=log.address,
                        position_token_address=self._position_token_address,
                        transaction_hash=transaction_hash,
                        transaction_from_address=_transaction_hash_from_dict[transaction_hash],
                        log_index=log.log_index,
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                        sender=None,  # decoded_data["sender"],
                        recipient=None,  # decoded_data["recipient"],
                        amount0=amount0,
                        amount1=amount1,
                        current_point=current_point,
                        fee=decoded_data["fee"],
                        sell_x_earn_y=decoded_data["sellXEarnY"],
                        token0_address=pool_data.get("token0_address"),
                        token1_address=pool_data.get("token1_address"),
                    ),
                )

    def get_pool_price(self, logs):
        if not logs:
            return
        block_info = {log.block_number: log.block_timestamp for log in logs}

        pool_prices = collect_pool_prices(self._exist_pools, logs, self._multicall_helper)
        prices = format_value_records(self._exist_pools, self._factory_address, pool_prices, block_info)
        current_price = None
        for price in prices:
            self._collect_item(IzumiPoolPrice.type(), price)
            if current_price is None or price.block_number > current_price.block_number:
                current_price = IzumiPoolCurrentPrice(
                    factory_address=price.factory_address,
                    pool_address=price.pool_address,
                    sqrt_price_x96=price.sqrt_price_x96,
                    current_point=price.current_point,
                    liquidity=price.liquidity,
                    liquidity_x=price.liquidity_x,
                    block_number=price.block_number,
                    block_timestamp=price.block_timestamp,
                )
        if current_price:
            self._collect_item(IzumiPoolCurrentPrice.type(), current_price)

    def _process(self, **kwargs):
        self._data_buff[IzumiPool.type()].sort(key=lambda x: x.block_number)
        self._data_buff[IzumiPoolPrice.type()].sort(key=lambda x: x.block_number)
        self._data_buff[IzumiPoolCurrentPrice.type()].sort(key=lambda x: x.block_number)


def format_value_records(exist_pools, factory_address, pool_prices, block_info):
    prices = []
    for key, pool_data in pool_prices.items():
        pool_address, block_number = key
        if pool_address in exist_pools:
            prices.append(
                IzumiPoolPrice(
                    factory_address=factory_address,
                    pool_address=pool_address,
                    sqrt_price_x96=pool_data["sqrt_price_x96"],
                    current_point=pool_data["current_point"],
                    liquidity=pool_data["liquidity"],
                    liquidity_x=pool_data["liquidity_x"],
                    block_number=block_number,
                    block_timestamp=block_info[block_number],
                )
            )
    return prices


def get_exist_pools(db_service, position_token_address):
    if not db_service:
        return {}

    session = db_service.get_service_session()
    try:
        result = (
            session.query(UniswapV3Pools)
            .filter(UniswapV3Pools.position_token_address == hex_str_to_bytes(position_token_address))
            .all()
        )
        history_pools = {}
        if result is not None:
            for item in result:
                pool_key = bytes_to_hex_str(item.pool_address)
                history_pools[pool_key] = {
                    "pool_address": pool_key,
                    "position_token_address": bytes_to_hex_str(item.position_token_address),
                    "token0_address": bytes_to_hex_str(item.token0_address),
                    "token1_address": bytes_to_hex_str(item.token1_address),
                    "fee": item.fee,
                    "point_delta": item.point_delta,
                    "block_number": item.block_number,
                    "pool_id": item.pool_id,
                }

    except Exception as e:
        raise e
    finally:
        session.close()

    return history_pools


def collect_pool_prices(exist_pools, logs, multicall_helper):
    pool_block_set = set()
    for log in logs:
        address = log.address
        current_topic0 = log.topic0
        block_number = log.block_number
        if address in exist_pools and (
            current_topic0 == SWAP_EVENT.get_signature()
            or current_topic0
            in [
                INCREASE_LIQUIDITY_EVENT.get_signature(),
                UPDATE_LIQUIDITY_EVENT.get_signature(),
                DECREASE_LIQUIDITY_EVENT.get_signature(),
                # position_token_address change event
                MINT_EVENT.get_signature(),
                BURN_EVENT.get_signature(),
            ]
        ):
            pool_block_set.add((address, block_number))

    state_calls = []
    for address, block_number in pool_block_set:
        state_calls.append(
            Call(
                target=address,
                function_abi=SLOT0_FUNCTION,
                block_number=block_number,
            )
        )
    multicall_helper.execute_calls(state_calls)

    pool_prices_map = {}
    for call in state_calls:
        pool_address = call.target
        block_number = call.block_number
        pool_data = {
            "sqrt_price_x96": call.returns["sqrtPrice_96"],
            "current_point": call.returns["currentPoint"],
            "liquidity": call.returns["liquidity"],
            "liquidity_x": call.returns["liquidity_x"],
            "block_number": block_number,
        }
        pool_prices_map[pool_address, block_number] = pool_data

    return pool_prices_map


def collect_swap_new_pools(position_token_address, factory_address, swap_pools, multicall_helper):
    pool_factory_calls = []
    for pool in swap_pools:
        pool_factory_calls.append(
            Call(
                target=pool["address"],
                function_abi=FACTORY_FUNCTION,
                block_number=pool["block_number"],
                user_defined_k=pool["block_timestamp"],
            )
        )

    multicall_helper.execute_calls(pool_factory_calls)

    eligible_pools = []
    eligible_pools_with_info = {}
    for call in pool_factory_calls:
        if "factory" in call.returns and call.returns["factory"] == factory_address:
            eligible_pools.append(
                {
                    "block_number": call.block_number,
                    "address": call.target,
                    "block_timestamp": call.user_defined_k,
                }
            )
    if len(eligible_pools) == 0:
        return eligible_pools_with_info

    pool_info_calls = []
    for pool in eligible_pools:
        pool_info_calls += [
            Call(
                target=pool["address"],
                function_abi=TOKEN0_FUNCTION,
                block_number=pool["block_number"],
                user_defined_k=pool["block_timestamp"],
            ),
            Call(
                target=pool["address"],
                function_abi=TOKEN1_FUNCTION,
                block_number=pool["block_number"],
                user_defined_k=pool["block_timestamp"],
            ),
            Call(
                target=pool["address"],
                function_abi=POINT_DELTA_FUNCTION,
                block_number=pool["block_number"],
                user_defined_k=pool["block_timestamp"],
            ),
            # Fee Function
        ]
    multicall_helper.execute_calls(pool_info_calls)

    for call in pool_info_calls:
        pool_address = call.target
        if pool_address not in eligible_pools_with_info:
            eligible_pools_with_info[pool_address] = {
                "position_token_address": position_token_address,
                "pool_address": pool_address,
                "block_number": call.block_number,
                "block_timestamp": call.user_defined_k,
            }
        if "tokenX" in call.returns:
            eligible_pools_with_info[pool_address]["token0_address"] = call.returns["tokenX"]
        if "tokenY" in call.returns:
            eligible_pools_with_info[pool_address]["token1_address"] = call.returns["tokenY"]
        if "pointDelta" in call.returns:
            eligible_pools_with_info[pool_address]["point_delta"] = call.returns["pointDelta"]

    return eligible_pools_with_info
