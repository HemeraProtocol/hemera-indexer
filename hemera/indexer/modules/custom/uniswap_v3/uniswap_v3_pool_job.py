import json
import logging
from collections import defaultdict

import eth_abi

from hemera.indexer.domain.log import Log
from hemera.indexer.domain.transaction import Transaction
from hemera.indexer.executors.batch_work_executor import BatchWorkExecutor
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.modules.custom import common_utils
from hemera.indexer.modules.custom.uniswap_v3.domains.feature_uniswap_v3 import (
    UniswapV3Pool,
    UniswapV3PoolCurrentPrice,
    UniswapV3PoolPrice,
    UniswapV3SwapEvent,
)
from hemera.indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from hemera.indexer.modules.custom.uniswap_v3.uniswapv3_abi import (
    BURN_EVENT,
    DECREASE_LIQUIDITY_EVENT,
    FACTORY_FUNCTION,
    FEE_FUNCTION,
    GET_POOL_FUNCTION,
    INCREASE_LIQUIDITY_EVENT,
    MINT_EVENT,
    OWNER_OF_FUNCTION,
    POOL_CREATED_EVENT,
    POSITIONS_FUNCTION,
    SLOT0_FUNCTION,
    SWAP_EVENT,
    TICK_SPACING_FUNCTION,
    TOKEN0_FUNCTION,
    TOKEN1_FUNCTION,
    UPDATE_LIQUIDITY_EVENT,
)
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from hemera.indexer.utils.rpc_utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)

FUNCTION_EVENT_LIST = [
    POSITIONS_FUNCTION,
    GET_POOL_FUNCTION,
    SLOT0_FUNCTION,
    POOL_CREATED_EVENT,
    SWAP_EVENT,
    OWNER_OF_FUNCTION,
    FACTORY_FUNCTION,
    FEE_FUNCTION,
    TOKEN0_FUNCTION,
    TOKEN1_FUNCTION,
    TICK_SPACING_FUNCTION,
    INCREASE_LIQUIDITY_EVENT,
    BURN_EVENT,
    UPDATE_LIQUIDITY_EVENT,
    DECREASE_LIQUIDITY_EVENT,
    MINT_EVENT,
]
UNISWAP_V3_ABI = [fe.get_abi() for fe in FUNCTION_EVENT_LIST]


class ExportUniSwapV3PoolJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [UniswapV3Pool, UniswapV3PoolPrice, UniswapV3PoolCurrentPrice, UniswapV3SwapEvent]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._service = kwargs["config"].get("db_service")
        self._abi_list = UNISWAP_V3_ABI
        self._batch_size = kwargs["batch_size"]

        config = kwargs["config"]["uniswap_v3_pool_job"]
        self._position_token_address = config.get("position_token_address").lower()
        self._factory_address = config.get("factory_address").lower()

        self._create_pool_topic0 = POOL_CREATED_EVENT.get_signature()
        self._pool_swap_topic0 = SWAP_EVENT.get_signature()

        self._exist_pools = get_exist_pools(self._service, self._position_token_address)
        self._max_worker = kwargs["max_workers"]

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
        # collect pool by create event
        self.get_pools()

        # collect swap event
        self.get_swap_event()

        # get prices
        logs = self._data_buff[Log.type()]
        grouped_logs = defaultdict(list)
        for log in logs:
            key = (log.address, log.topic0, log.block_number)
            grouped_logs[key].append(log)

        max_log_index_records = []
        for group in grouped_logs.values():
            max_log_index_record = max(group, key=lambda x: x.log_index)
            max_log_index_records.append(max_log_index_record)

        self._batch_work_executor.execute(
            max_log_index_records, self._collect_batch, len(max_log_index_records), split_logs
        )
        self._batch_work_executor.wait()

    def get_pools(self):
        maybe_unknown_event_in_swap_eventy_dict = defaultdict(dict)

        logs = self._data_buff[Log.type()]
        for log in logs:
            log_address = log.address
            if log_address not in self._exist_pools:
                # collect pools by create event
                if log_address == self._factory_address and log.topic0 == POOL_CREATED_EVENT.get_signature():
                    decoded_data = POOL_CREATED_EVENT.decode_log(log)
                    pool_address = decoded_data["pool"]
                    new_pool_dict = {
                        "position_token_address": self._position_token_address,
                        "token0_address": decoded_data["token0"],
                        "token1_address": decoded_data["token1"],
                        "fee": decoded_data["fee"],
                        "tick_spacing": decoded_data["tickSpacing"],
                        "pool_address": pool_address,
                        "block_number": log.block_number,
                    }
                    self._exist_pools[log_address] = new_pool_dict

                    uniswap_v3_pool = UniswapV3Pool(
                        block_timestamp=log.block_timestamp, factory_address=self._factory_address, **new_pool_dict
                    )

                    self._collect_domain(uniswap_v3_pool)
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
            UNISWAP_V3_ABI,
            self._web3,
            self._batch_web3_provider.make_request,
            self._is_batch,
            self._batch_size,
            self._max_worker,
        )
        for pool_address, pool_dict in pools_get_from_swap_event.items():
            if pool_address not in self._exist_pools:
                self._exist_pools[pool_address] = pool_dict
                uniswap_v3_pool = UniswapV3Pool(factory_address=self._factory_address, fee=0, **pool_dict)

                self._collect_domain(uniswap_v3_pool)

    def get_swap_event(self):
        transactions = self._data_buff[Transaction.type()]
        _transaction_hash_from_dict = {}
        for transaction in transactions:
            _transaction_hash_from_dict[transaction.hash] = transaction.from_address

        logs = self._data_buff[Log.type()]

        for log in logs:
            if log.address not in self._exist_pools:
                continue
            # Collect swap logs
            if log.topic0 == SWAP_EVENT.get_signature():
                transaction_hash = log.transaction_hash
                decoded_data = SWAP_EVENT.decode_log(log)

                amount0 = decoded_data["amount0"]
                amount1 = decoded_data["amount1"]
                sqrt_price_x96 = decoded_data["sqrtPriceX96"]
                liquidity = decoded_data["liquidity"]
                tick = decoded_data["tick"]
                pool_data = self._exist_pools[log.address]
                self._collect_item(
                    UniswapV3SwapEvent.type(),
                    UniswapV3SwapEvent(
                        pool_address=log.address,
                        position_token_address=self._position_token_address,
                        transaction_hash=transaction_hash,
                        transaction_from_address=_transaction_hash_from_dict[transaction_hash],
                        log_index=log.log_index,
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                        sender=decoded_data["sender"],
                        recipient=decoded_data["recipient"],
                        amount0=amount0,
                        amount1=amount1,
                        liquidity=liquidity,
                        tick=tick,
                        sqrt_price_x96=sqrt_price_x96,
                        token0_address=pool_data.get("token0_address"),
                        token1_address=pool_data.get("token1_address"),
                    ),
                )

    def _collect_batch(self, logs_dict):
        if not logs_dict:
            return
        token_address = next(iter(logs_dict))
        logs = logs_dict[token_address]
        block_info = {log.block_number: log.block_timestamp for log in logs}

        liquidity_list = [  # lp change event
            INCREASE_LIQUIDITY_EVENT.get_signature(),
            UPDATE_LIQUIDITY_EVENT.get_signature(),
            DECREASE_LIQUIDITY_EVENT.get_signature(),
            # position_token_address change event
            MINT_EVENT.get_signature(),
            BURN_EVENT.get_signature(),
        ]

        pool_prices = collect_pool_prices(
            self._pool_swap_topic0,
            liquidity_list,
            self._exist_pools,
            logs,
            self._web3,
            self._batch_web3_provider.make_request,
            self._is_batch,
            self._abi_list,
            self._batch_size,
            self._max_worker,
        )
        prices = format_value_records(self._exist_pools, self._factory_address, pool_prices, block_info)
        current_price = None
        for price in prices:
            self._collect_item(UniswapV3PoolPrice.type(), price)
            if current_price is None or price.block_number > current_price.block_number:
                current_price = UniswapV3PoolCurrentPrice(
                    factory_address=price.factory_address,
                    pool_address=price.pool_address,
                    sqrt_price_x96=price.sqrt_price_x96,
                    tick=price.tick,
                    block_number=price.block_number,
                    block_timestamp=price.block_timestamp,
                )
        if current_price:
            self._collect_item(UniswapV3PoolCurrentPrice.type(), current_price)

    def _process(self, **kwargs):
        self._data_buff[UniswapV3Pool.type()].sort(key=lambda x: x.block_number)
        self._data_buff[UniswapV3PoolPrice.type()].sort(key=lambda x: x.block_number)
        self._data_buff[UniswapV3PoolCurrentPrice.type()].sort(key=lambda x: x.block_number)


def format_value_records(exist_pools, factory_address, pool_prices, block_info):
    prices = []
    for key, pool_data in pool_prices.items():
        pool_address, block_number = key
        if pool_address in exist_pools:
            prices.append(
                UniswapV3PoolPrice(
                    factory_address=factory_address,
                    pool_address=pool_address,
                    sqrt_price_x96=pool_data["sqrtPriceX96"],
                    tick=pool_data["tick"],
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
            .filter(UniswapV3Pools.position_token_address == bytes.fromhex(position_token_address[2:]))
            .all()
        )
        history_pools = {}
        if result is not None:
            for item in result:
                pool_key = "0x" + item.pool_address.hex()
                history_pools[pool_key] = {
                    "pool_address": pool_key,
                    "position_token_address": "0x" + item.position_token_address.hex(),
                    "token0_address": "0x" + item.token0_address.hex(),
                    "token1_address": "0x" + item.token1_address.hex(),
                    "fee": item.fee,
                    "tick_spacing": item.tick_spacing,
                    "block_number": item.block_number,
                }

    except Exception as e:
        print(e)
        raise e
    finally:
        session.close()

    return history_pools


def collect_pool_prices(
    target0_topic0,
    target1_topic0_list,
    exist_pools,
    logs,
    web3,
    make_requests,
    is_batch,
    abi_list,
    batch_size,
    max_workers,
):
    pool_block_set = set()
    for log in logs:
        address = log.address
        current_topic0 = log.topic0
        block_number = log.block_number
        if address in exist_pools and (current_topic0 == target0_topic0 or current_topic0 in target1_topic0_list):
            pool_block_set.add((address, block_number))
    requests = []
    for address, block_number in pool_block_set:
        requests.append(
            {
                "pool_address": address,
                "block_number": block_number,
            }
        )
    pool_prices = slot0_rpc_requests(web3, make_requests, requests, is_batch, abi_list, batch_size, max_workers)
    pool_prices_map = {}
    for data in pool_prices:
        pool_data = {
            "sqrtPriceX96": data["sqrtPriceX96"],
            "tick": data["tick"],
            "block_number": data["block_number"],
        }
        pool_prices_map[data["pool_address"], data["block_number"]] = pool_data
    return pool_prices_map


def collect_swap_new_pools(
    position_token_address, factory_address, swap_pools, abi_list, web3, make_requests, is_batch, batch_size, max_worker
):
    factory_infos = common_utils.simple_get_rpc_requests(
        web3, make_requests, swap_pools, is_batch, abi_list, "factory", "address", batch_size, max_worker
    )
    uniswap_pools = []
    need_add = {}
    for data in factory_infos:
        if "factory" in data and data["factory"] == factory_address:
            uniswap_pools.append(
                {
                    "block_number": data["block_number"],
                    "address": data["address"],
                    "block_timestamp": data["block_timestamp"],
                }
            )
    if len(uniswap_pools) == 0:
        return need_add
    token0_infos = common_utils.simple_get_rpc_requests(
        web3, make_requests, uniswap_pools, is_batch, abi_list, "token0", "address", batch_size, max_worker
    )
    token1_infos = common_utils.simple_get_rpc_requests(
        web3, make_requests, token0_infos, is_batch, abi_list, "token1", "address", batch_size, max_worker
    )
    tick_infos = common_utils.simple_get_rpc_requests(
        web3, make_requests, token1_infos, is_batch, abi_list, "tickSpacing", "address", batch_size, max_worker
    )
    # uniswap v3 pool have no fee function
    # fee_infos = simple_get_rpc_requests(web3, make_requests, tick_infos, is_batch, abi_list, "fee", "address")
    for data in tick_infos:
        pool_address = data["address"]
        if "token0" in data and "token1" in data and "tickSpacing" in data:
            new_pool = {
                "position_token_address": position_token_address,
                "token0_address": data["token0"],
                "token1_address": data["token1"],
                # "fee": data["fee"],
                "tick_spacing": data["tickSpacing"],
                "pool_address": pool_address,
                "block_number": data["block_number"],
                "block_timestamp": data["block_timestamp"],
            }
            need_add[pool_address] = new_pool
    return need_add


def split_logs(logs):
    log_dict = defaultdict(list)
    for data in logs:
        log_dict[data.address].append(data)

    for token_address, data in log_dict.items():
        yield {token_address: data}


def slot0_rpc_requests(web3, make_requests, requests, is_batch, abi_list, batch_size, max_worker):
    if len(requests) == 0:
        return []
    fn_name = "slot0"
    function_abi = next((abi for abi in abi_list if abi["name"] == fn_name and abi["type"] == "function"), None)
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    def process_batch(batch):
        parameters = common_utils.build_no_input_method_data(web3, batch, fn_name, abi_list)
        token_name_rpc = list(generate_eth_call_json_rpc(parameters))

        if is_batch:
            response = make_requests(params=json.dumps(token_name_rpc))
        else:
            response = [make_requests(params=json.dumps(token_name_rpc[0]))]

        token_infos = []
        for data in list(zip_rpc_response(parameters, response)):
            result = rpc_response_to_result(data[1])
            pool = data[0]
            value = result[2:] if result is not None else None
            try:
                decoded_data = eth_abi.decode(output_types, bytes.fromhex(value))
                pool["sqrtPriceX96"] = decoded_data[0]
                pool["tick"] = decoded_data[1]
            except Exception as e:
                logger.error(f"Decoding {fn_name} failed. " f"rpc response: {result}. " f"exception: {e}")
            token_infos.append(pool)
        return token_infos

    executor = BatchWorkExecutor(
        starting_batch_size=batch_size,
        max_workers=max_worker,
        job_name=f"slot0_rpc_requests_{fn_name}",
    )

    all_token_infos = []

    def work_handler(batch):
        nonlocal all_token_infos
        batch_results = process_batch(batch)
        all_token_infos.extend(batch_results)

    executor.execute(requests, work_handler, total_items=len(requests))
    executor.wait()

    return all_token_infos
