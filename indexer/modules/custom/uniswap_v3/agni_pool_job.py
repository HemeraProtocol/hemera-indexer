import json
import logging
from collections import defaultdict

import eth_abi

from common.utils.abi_code_utils import decode_log
from indexer.domain import dict_to_dataclass
from indexer.domain.log import Log
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.uniswap_v3.agni_abi import (
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
from indexer.modules.custom.uniswap_v3.domains.feature_uniswap_v3 import (
    AgniV3Pool,
    AgniV3PoolCurrentPrice,
    AgniV3PoolPrice,
)
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.rpc_utils import rpc_response_to_result, zip_rpc_response

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
AGNI_ABI = [fe.get_abi() for fe in FUNCTION_EVENT_LIST]

liquidity_event_list = [INCREASE_LIQUIDITY_EVENT, UPDATE_LIQUIDITY_EVENT, DECREASE_LIQUIDITY_EVENT]
LIQUIDITY_EVENT_TOPIC0_LIST = [e.get_signature() for e in liquidity_event_list]

nft_event_list = [MINT_EVENT, BURN_EVENT]
NFT_EVENT_TOPIC0_LIST = [e.get_signature() for e in nft_event_list]


class ExportAgniV3PoolJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [AgniV3Pool, AgniV3PoolPrice, AgniV3PoolCurrentPrice]
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
        self._abi_list = AGNI_ABI
        self._batch_size = kwargs["batch_size"]

        config = kwargs["config"]["agni_pool_job"]
        self._position_token_address = config.get("position_token_address").lower()
        self._factory_address = config.get("factory_address").lower()
        self._create_pool_topic0 = POOL_CREATED_EVENT.get_signature()
        self._pool_swap_topic0 = SWAP_EVENT.get_signature()

        self._exist_pools = get_exist_pools(self._service, self._position_token_address)
        self._max_worker = kwargs["max_workers"]

    def get_filter(self):
        liquidity_topic0_list = LIQUIDITY_EVENT_TOPIC0_LIST + NFT_EVENT_TOPIC0_LIST
        liquidity_topic0_list.append(self._pool_swap_topic0)
        liquidity_topic0_list.append(self._create_pool_topic0)

        return TransactionFilterByLogs(
            [
                TopicSpecification(topics=liquidity_topic0_list),
            ]
        )

    def _process(self, **kwargs):
        logs = self._data_buff[Log.type()]
        grouped_logs = defaultdict(list)
        for log in logs:
            key = (log.address, log.topic0, log.block_number)
            grouped_logs[key].append(log)

        max_log_index_records = []
        for group in grouped_logs.values():
            max_log_index_record = max(group, key=lambda x: x.log_index)
            max_log_index_records.append(max_log_index_record)

        # first collect pool info
        need_add_in_exists_pools = update_exist_pools(
            self._position_token_address,
            self._factory_address,
            self._exist_pools,
            self._create_pool_topic0,
            self._pool_swap_topic0,
            LIQUIDITY_EVENT_TOPIC0_LIST,
            max_log_index_records,
            self._abi_list,
            self._web3,
            self._batch_web3_provider.make_request,
            self._is_batch,
            self._batch_size,
            self._max_worker,
        )
        self._exist_pools.update(need_add_in_exists_pools)

        for pools in format_pool_item(need_add_in_exists_pools):
            self._collect_item(AgniV3Pool.type(), pools)

        self._batch_work_executor.execute(
            max_log_index_records, self._collect_batch, len(max_log_index_records), split_logs
        )
        self._batch_work_executor.wait()

        self._data_buff[AgniV3Pool.type()].sort(key=lambda x: x.block_number)
        self._data_buff[AgniV3PoolPrice.type()].sort(key=lambda x: x.block_number)
        self._data_buff[AgniV3PoolCurrentPrice.type()].sort(key=lambda x: x.block_number)

    def _collect_batch(self, logs_dict):
        if not logs_dict:
            return

        token_address = next(iter(logs_dict))
        logs = logs_dict[token_address]
        block_info = {log.block_number: log.block_timestamp for log in logs}
        liquidity_keys_list = LIQUIDITY_EVENT_TOPIC0_LIST
        liquidity_list = NFT_EVENT_TOPIC0_LIST + liquidity_keys_list

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
            self._collect_item(AgniV3PoolPrice.type(), price)
            if current_price is None or price.block_number > current_price.block_number:
                current_price = AgniV3PoolCurrentPrice(
                    factory_address=price.factory_address,
                    pool_address=price.pool_address,
                    sqrt_price_x96=price.sqrt_price_x96,
                    tick=price.tick,
                    block_number=price.block_number,
                    block_timestamp=price.block_timestamp,
                )
        if current_price:
            self._collect_item(AgniV3PoolCurrentPrice.type(), current_price)


def format_pool_item(new_pools):
    result = []
    for pool_address, pool in new_pools.items():
        result.append(dict_to_dataclass(pool, AgniV3Pool))
    return result


def format_value_records(exist_pools, factory_address, pool_prices, block_info):
    prices = []
    for address, pool_data in pool_prices.items():
        if address not in exist_pools.keys():
            continue
        info = exist_pools.get(address)
        block_number = pool_data["block_number"]
        prices.append(
            AgniV3PoolPrice(
                factory_address=factory_address,
                pool_address=address,
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


def update_exist_pools(
    position_token_address,
    factory_address,
    exist_pools,
    create_topic0,
    swap_topic0,
    liquidity_topic0_list,
    logs,
    abi_list,
    web3,
    make_requests,
    is_batch,
    batch_size,
    max_worker,
):
    need_add = {}
    swap_pools = []
    for log in logs:
        address = log.address
        if address in exist_pools:
            continue
        current_topic0 = log.topic0
        if factory_address == address and create_topic0 == current_topic0:
            decoded_data = POOL_CREATED_EVENT.decode_log(log)
            pool_address = decoded_data["pool"]

            new_pool = {
                "position_token_address": position_token_address,
                "token0_address": decoded_data["token0"],
                "token1_address": decoded_data["token1"],
                "fee": decoded_data["fee"],
                "tick_spacing": decoded_data["tickSpacing"],
                "pool_address": pool_address,
                "block_number": log.block_number,
            }
            need_add[pool_address] = new_pool
        elif swap_topic0 == current_topic0 or current_topic0 in liquidity_topic0_list:
            # if the address created by factory_address ,collect it
            swap_pools.append({"address": address, "block_number": log.block_number})
    swap_new_pools = collect_swap_new_pools(
        position_token_address,
        factory_address,
        swap_pools,
        abi_list,
        web3,
        make_requests,
        is_batch,
        batch_size,
        max_worker,
    )
    need_add.update(swap_new_pools)
    return need_add


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
        pool_prices_map[data["pool_address"]] = pool_data
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
