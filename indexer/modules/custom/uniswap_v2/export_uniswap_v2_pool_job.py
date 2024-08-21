import configparser
import json
import logging
import os
import threading
from collections import defaultdict
from queue import Queue
from typing import List, Tuple, cast

import eth_abi
from web3.types import ABIEvent

from common import models
from indexer.domain import dict_to_dataclass
from indexer.domain.current_token_balance import CurrentTokenBalance
from indexer.domain.log import Log
from indexer.domain.token_balance import TokenBalance
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.uniswap_v2.constants import RESERVES_ABI, RESERVES_PREFIX, UNISWAP_V2_ABI
from indexer.modules.custom.uniswap_v2.domain.feature_uniswap_v2 import (
    UniswapV2CurrentLiquidityHolding,
    UniswapV2LiquidityHolding,
    UniswapV2Pool,
    UniswapV2PoolCurrentReserves,
    UniswapV2PoolCurrentTotalSupply,
    UniswapV2PoolReserves,
    UniswapV2PoolTotalSupply,
)
from indexer.modules.custom.uniswap_v2.models.feature_uniswap_v2_pools import UniswapV2Pools
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.abi import decode_log, encode_abi, function_abi_to_4byte_selector_str
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.UNISWAP_V2_INFO.value


class ExportUniSwapV2InfoJob(FilterTransactionDataJob):
    dependency_types = [Log, TokenBalance, CurrentTokenBalance]
    output_types = [
        UniswapV2Pool,
        UniswapV2PoolTotalSupply,
        UniswapV2PoolCurrentTotalSupply,
        UniswapV2PoolReserves,
        UniswapV2PoolCurrentReserves,
        UniswapV2LiquidityHolding,
        UniswapV2CurrentLiquidityHolding,
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._service = (kwargs["config"].get("db_service"),)
        self._load_config("config.ini")
        self._abi_list = UNISWAP_V2_ABI
        self._exist_pools = get_exist_pools(self._service, self._factory_address)
        self._batch_size = kwargs["batch_size"]
        self._max_worker = kwargs["max_workers"]

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=[self._factory_address], topics=[self._create_pool_topic0]),
                TopicSpecification(topics=[self._pool_mint_topic0, self._pool_burn_topic0, self._pool_sync_topic0]),
            ]
        )

    def _load_config(self, filename):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)

        try:
            self._factory_address = config.get("info", "factory_address").lower()
            self._create_pool_topic0 = config.get("info", "create_pool_topic0").lower()
            self._pool_mint_topic0 = config.get("info", "pool_mint_topic0").lower()
            self._pool_burn_topic0 = config.get("info", "pool_burn_topic0").lower()
            self._pool_sync_topic0 = config.get("info", "pool_sync_topic0").lower()
            self._pool_transfer_topic0 = config.get("info", "pool_transfer_topic0").lower()
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]

        # first collect pool info
        need_add_in_exists_pools, active_pools = update_exist_pools(
            self._factory_address,
            self._exist_pools,
            self._create_pool_topic0,
            self._pool_mint_topic0,
            self._pool_burn_topic0,
            logs,
            self._abi_list,
            self._web3,
            self._batch_web3_provider.make_request,
            self._is_batch,
            self._batch_size,
            self._max_worker,
        )
        self._exist_pools.update(need_add_in_exists_pools)

        for pools in format_pool_item(need_add_in_exists_pools):
            self._collect_item(UniswapV2Pool.type(), pools)

        self._batch_work_executor.execute(
            active_pools, self._collect_total_supply_batch, len(active_pools), split_by_dict_address
        )
        self._batch_work_executor.wait()

        # collect pool holds reserves
        need_reserves_list = filter_logs_to_list(logs, self._exist_pools)
        self._batch_work_executor.execute(
            need_reserves_list, self._collect_pool_balance_batch, len(active_pools), split_by_dict_address
        )
        self._batch_work_executor.wait()

        # collect user holding
        token_balances = self._data_buff[TokenBalance.type()]
        self._batch_work_executor.execute(
            token_balances,
            self._collect_wallet_holding_batch,
            total_items=len(token_balances),
        )

        self._batch_work_executor.wait()
        current_token_balances = self._data_buff[CurrentTokenBalance.type()]
        self._batch_work_executor.execute(
            current_token_balances,
            self._collect_wallet_current_batch,
            total_items=len(current_token_balances),
        )
        self._batch_work_executor.wait()

    def _collect_pool_balance_batch(self, need_reserves_dict):
        if need_reserves_dict is None or len(need_reserves_dict) == 0:
            return
        pool_address = next(iter(need_reserves_dict))
        need_reserves_list = need_reserves_dict[pool_address]
        reserve_list = batch_get_reserves(
            self._web3, self._batch_web3_provider.make_request, need_reserves_list, self._is_batch
        )
        current_reserves = None
        for data in reserve_list:
            block_timestamp_last = data["block_timestamp_last"]
            info = UniswapV2PoolReserves(
                pool_address=data["address"],
                called_block_number=data["block_number"],
                called_block_timestamp=data["block_timestamp"],
                reserve0=data["reserve0"],
                reserve1=data["reserve1"],
                block_timestamp_last=block_timestamp_last,
            )
            self._collect_item(UniswapV2PoolReserves.type(), info)

            if current_reserves is None or block_timestamp_last > current_reserves.block_timestamp_last:
                current_reserves = UniswapV2PoolCurrentReserves(
                    pool_address=data["address"],
                    block_number=data["block_number"],
                    block_timestamp=data["block_timestamp"],
                    reserve0=data["reserve0"],
                    reserve1=data["reserve1"],
                    block_timestamp_last=block_timestamp_last,
                )

        self._collect_item(UniswapV2PoolCurrentReserves.type(), current_reserves)

    def _collect_total_supply_batch(self, active_pools):
        if active_pools is None or len(active_pools) == 0:
            return
        pool_address = next(iter(active_pools))
        pool_total_supply_records, current_total_supply = collect_pool_total_supply(
            active_pools[pool_address],
            self._abi_list,
            self._web3,
            self._batch_web3_provider.make_request,
            self._is_batch,
            self._batch_size,
            self._max_worker,
        )
        for data in pool_total_supply_records:
            self._collect_item(UniswapV2PoolTotalSupply.type(), data)

        self._collect_item(UniswapV2PoolCurrentTotalSupply.type(), current_total_supply)

    def _collect_wallet_holding_batch(self, token_balances) -> None:
        if token_balances is None or len(token_balances) == 0:
            return
        for token_balance in token_balances:
            token_address = token_balance.token_address
            if token_address not in self._exist_pools:
                continue
            self._collect_item(UniswapV2LiquidityHolding.type(), parse_balance_to_holding(token_balance))

    def _collect_wallet_current_batch(self, current_token_balances) -> None:
        if current_token_balances is None or len(current_token_balances) == 0:
            return
        for current_token_balance in current_token_balances:
            token_address = current_token_balance.token_address
            if token_address not in self._exist_pools:
                continue
            self._collect_item(UniswapV2CurrentLiquidityHolding.type(), parse_current_to_holding(current_token_balance))

    def _process(self):
        self._data_buff[UniswapV2Pool.type()].sort(key=lambda x: x.called_block_number)
        self._data_buff[UniswapV2PoolTotalSupply.type()].sort(key=lambda x: x.called_block_number)
        self._data_buff[UniswapV2PoolReserves.type()].sort(key=lambda x: x.called_block_number)
        self._data_buff[UniswapV2LiquidityHolding.type()].sort(key=lambda x: x.called_block_number)
        self._data_buff[UniswapV2PoolCurrentTotalSupply.type()].sort(key=lambda x: x.block_number)
        self._data_buff[UniswapV2PoolCurrentReserves.type()].sort(key=lambda x: x.block_number)
        self._data_buff[UniswapV2CurrentLiquidityHolding.type()].sort(key=lambda x: x.block_number)


def parse_current_to_holding(token_balance: CurrentTokenBalance):
    return UniswapV2CurrentLiquidityHolding(
        pool_address=token_balance.token_address,
        wallet_address=token_balance.address,
        balance=token_balance.balance,
        block_number=token_balance.block_number,
        block_timestamp=token_balance.block_timestamp,
    )


def parse_balance_to_holding(token_balance: TokenBalance):
    return UniswapV2LiquidityHolding(
        pool_address=token_balance.token_address,
        wallet_address=token_balance.address,
        balance=token_balance.balance,
        called_block_number=token_balance.block_number,
        called_block_timestamp=token_balance.block_timestamp,
    )


def filter_logs_to_list(logs, exist_pools):
    seen = set()
    result = []

    for data in logs:
        address = data.address
        block_number = data.block_number
        block_timestamp = data.block_timestamp

        if address in exist_pools and (address, block_number) not in seen:
            result.append({"address": address, "block_number": block_number, "block_timestamp": block_timestamp})
            seen.add((address, block_number))

    return result


def encode_get_reserves_parameter():
    return encode_abi(RESERVES_ABI, [], RESERVES_PREFIX)


def build_reserves_request_data(web3, need_call_list, data_key="address"):
    parameters = []

    for idx, token in enumerate(need_call_list):
        token_data = {
            "request_id": idx,
            "param_to": token[data_key],
            "param_number": hex(token["block_number"]),
        }
        token.update(token_data)

        try:
            token["param_data"] = encode_get_reserves_parameter()
        except Exception as e:
            logger.error(
                f"Encoding contract address {token[data_key]} for function getReserves failed. " f"Exception: {e}."
            )

        parameters.append(token)
    return parameters


def batch_get_reserves(web3, make_requests, requests, is_batch, data_key="address"):
    function_abi = RESERVES_ABI
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    parameters = build_reserves_request_data(web3, requests, data_key)

    reserves_rpc = list(generate_eth_call_json_rpc(parameters))
    if is_batch:
        response = make_requests(params=json.dumps(reserves_rpc))
    else:
        response = [make_requests(params=json.dumps(reserves_rpc[0]))]

    infos = []
    for data in list(zip_rpc_response(parameters, response)):
        result = rpc_response_to_result(data[1])
        token = data[0]
        value = result[2:] if result is not None else None
        try:
            decoded_data = eth_abi.decode(output_types, bytes.fromhex(value))
            token["reserve0"] = decoded_data[0]
            token["reserve1"] = decoded_data[1]
            token["block_timestamp_last"] = decoded_data[2]

        except Exception as e:
            logger.error(
                f"Decoding token info failed. "
                f"token: {token}. "
                f"fn: getReserves "
                f"rpc response: {result}. "
                f"exception: {e}"
            )
        infos.append(token)
    return infos


def format_pool_item(new_pools):
    result = []
    for pool_address, pool in new_pools.items():
        result.append(dict_to_dataclass(pool, UniswapV2Pool))
    return result


def get_exist_pools(db_service, factory_address):
    if not db_service:
        return {}

    session = db_service[0].get_service_session()
    try:
        result = (
            session.query(UniswapV2Pools)
            .filter(UniswapV2Pools.factory_address == bytes.fromhex(factory_address[2:]))
            .all()
        )
        history_pools = {}
        if result is not None:
            for item in result:
                pool_key = "0x" + item.pool_address.hex()
                history_pools[pool_key] = {
                    "pool_address": pool_key,
                    "token0_address": "0x" + item.token0_address.hex(),
                    "token1_address": "0x" + item.token1_address.hex(),
                    "length": item.length,
                    "called_block_number": item.called_block_number,
                }

    except Exception as e:
        print(e)
        raise e
    finally:
        session.close()

    return history_pools


def update_exist_pools(
    factory_address,
    exist_pools,
    create_topic0,
    mint_topic0,
    burn_topic0,
    logs,
    abi_list,
    web3,
    make_requests,
    is_batch,
    batch_size,
    max_worker,
):
    need_add = {}
    all_active_pools = {}
    first_active_pools = {}
    for log in logs:
        address = log.address
        current_topic0 = log.topic0
        if factory_address == address and create_topic0 == current_topic0:
            decoded_data = decode_logs("PairCreated", abi_list, log)
            pool_address = decoded_data["pair"]
            new_pool = {
                "factory_address": factory_address,
                "token0_address": decoded_data["token0"],
                "token1_address": decoded_data["token1"],
                "pool_address": pool_address,
                "length": decoded_data["length"],
                "called_block_number": log.block_number,
            }
            need_add[pool_address] = new_pool
        elif mint_topic0 == current_topic0 or burn_topic0 == current_topic0:
            # each address <-> its block_numbers and timestamps
            if address not in all_active_pools:
                all_active_pools[address] = set()
            all_active_pools[address].add((log.block_number, log.block_timestamp))
            # each address <->  one block_number
            if address not in first_active_pools and address not in exist_pools:
                first_active_pools[address] = log.block_number

    first_pools_list = [
        {"address": address, "block_number": block_number} for address, block_number in first_active_pools.items()
    ]

    swap_new_pools = collect_active_new_pools(
        factory_address, first_pools_list, abi_list, web3, make_requests, is_batch, batch_size, max_worker
    )
    need_add.update(swap_new_pools)

    # valid active pools
    active_pools = []
    for address, block_info in all_active_pools.items():
        if address in need_add or address in exist_pools:
            active_pools.extend(
                [
                    {"address": address, "block_number": block_number, "block_timestamp": block_timestamp}
                    for block_number, block_timestamp in block_info
                ]
            )

    return need_add, active_pools


def collect_pool_total_supply(
    need_collect_list, abi_list, web3, make_requests, is_batch, batch_size, max_worker
) -> Tuple[List[UniswapV2PoolTotalSupply], UniswapV2PoolCurrentTotalSupply]:
    # Call totalSupply
    total_supply_infos = common_utils.simple_get_rpc_requests(
        web3, make_requests, need_collect_list, is_batch, abi_list, "totalSupply", "address", batch_size, max_worker
    )

    # Initialize variables
    result_list = []
    current_supply = None

    for data in total_supply_infos:
        address = data["address"]
        block_number = data["block_number"]
        block_timestamp = data["block_timestamp"]
        total_supply = data["totalSupply"]

        # Create a UniswapV2PoolTotalSupply instance and add to result list
        pool_supply = UniswapV2PoolTotalSupply(
            pool_address=address,
            total_supply=total_supply,
            called_block_number=block_number,
            called_block_timestamp=block_timestamp,
        )
        result_list.append(pool_supply)

        # Determine the current supply (i.e., the one with the maximum block_number)
        if current_supply is None or block_number > current_supply.block_number:
            current_supply = UniswapV2PoolCurrentTotalSupply(
                pool_address=address,
                total_supply=total_supply,
                block_number=block_number,
                block_timestamp=block_timestamp,
            )

    return result_list, current_supply


def collect_active_new_pools(
    factory_address, active_pools, abi_list, web3, make_requests, is_batch, batch_size, max_worker
):
    factory_infos = common_utils.simple_get_rpc_requests(
        web3, make_requests, active_pools, is_batch, abi_list, "factory", "address", batch_size, max_worker
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
    for data in token1_infos:
        pool_address = data["address"]
        new_pool = {
            "factory_address": factory_address,
            "token0_address": data["token0"],
            "token1_address": data["token1"],
            "pool_address": pool_address,
            "called_block_number": data["block_number"],
        }
        need_add[pool_address] = new_pool
    return need_add


def decode_logs(fn_name, contract_abi, log):
    function_abi = next(
        (abi for abi in contract_abi if abi["name"] == fn_name and abi["type"] == "event"),
        None,
    )
    if not function_abi:
        raise ValueError("Function ABI not found")

    return decode_log(function_abi, log)


def split_by_dict_address(active_pools):
    log_dict = defaultdict(list)
    for data in active_pools:
        log_dict[data["address"]].append(data)

    for token_address, data in log_dict.items():
        yield {token_address: data}
