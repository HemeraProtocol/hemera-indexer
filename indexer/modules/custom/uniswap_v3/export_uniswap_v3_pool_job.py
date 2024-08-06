import configparser
import json
import logging
import os
import threading
from collections import defaultdict

import eth_abi

from common import models
from indexer.domain import dict_to_dataclass
from indexer.domain.log import Log
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.all_features_value_record import AllFeatureValueRecordUniswapV3Pool
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.uniswap_v3.constants import UNISWAP_V3_ABI
from indexer.modules.custom.uniswap_v3.domain.feature_uniswap_v3 import UniswapV3Pool
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from indexer.modules.custom.uniswap_v3.util import build_no_input_method_data
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.abi import decode_log
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.UNISWAP_V3_POOLS.value


class ExportUniSwapV3PoolJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [AllFeatureValueRecordUniswapV3Pool, UniswapV3Pool]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._service = (kwargs["config"].get("db_service"),)
        self._pool_prices = {}
        self._pool_prices_lock = threading.Lock()
        self._load_config("config.ini")
        self._abi_list = UNISWAP_V3_ABI
        self._exist_pools = get_exist_pools(self._service[0], self._nft_address)

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=[self._factory_address], topics=[self._create_pool_topic0]),
                TopicSpecification(topics=[self._pool_swap_topic0]),
            ]
        )

    def _load_config(self, filename):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)

        try:
            self._nft_address = config.get("info", "nft_address").lower()
            self._factory_address = config.get("info", "factory_address").lower()
            self._create_pool_topic0 = config.get("info", "create_pool_topic0").lower()
            self._pool_swap_topic0 = config.get("info", "pool_swap_topic0").lower()
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def _start(self):
        super()._start()

    def _collect(self, **kwargs):
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
            self._nft_address,
            self._factory_address,
            self._exist_pools,
            self._create_pool_topic0,
            self._pool_swap_topic0,
            max_log_index_records,
            self._abi_list,
            self._web3,
            self._batch_web3_provider.make_request,
            self._is_batch,
        )
        self._exist_pools.update(need_add_in_exists_pools)

        for pools in format_pool_item(need_add_in_exists_pools):
            self._collect_item(UniswapV3Pool.type(), pools)

        self._batch_work_executor.execute(max_log_index_records, self._collect_batch, len(max_log_index_records))
        self._batch_work_executor.wait()

    def _collect_batch(self, logs):

        pool_prices = collect_pool_prices([self._pool_swap_topic0], self._exist_pools, logs, self._abi_list)
        self.update_pool_prices(pool_prices)
        for record in format_value_records(self._exist_pools, pool_prices, FEATURE_ID):
            self._collect_item(AllFeatureValueRecordUniswapV3Pool.type(), record)

    def _process(self):
        self._data_buff[UniswapV3Pool.type()].sort(key=lambda x: x.called_block_number)
        self._data_buff[AllFeatureValueRecordUniswapV3Pool.type()].sort(key=lambda x: x.block_number)

    def update_pool_prices(self, new_pool_prices):
        if not new_pool_prices or len(new_pool_prices) == 0:
            return
        with self._pool_prices_lock:
            for address, new_data in new_pool_prices.items():
                if address in self._pool_prices:
                    current_data = self._pool_prices[address]
                    if new_data["block_number"] > current_data["block_number"] or (
                        new_data["block_number"] == current_data["block_number"]
                        and new_data["log_index"] > current_data["log_index"]
                    ):
                        self._pool_prices[address] = new_data
                else:
                    self._pool_prices[address] = new_data


def format_pool_item(new_pools):
    result = []
    for pool_address, pool in new_pools.items():
        result.append(dict_to_dataclass(pool, UniswapV3Pool))
    return result


def format_value_records(exist_pools, pool_prices, feature_id):
    result = []

    for address, pool_data in pool_prices.items():
        if address not in exist_pools.keys():
            continue
        info = exist_pools.get(address)
        block_number = pool_data["block_number"]
        value = {
            "token0_address": info["token0_address"],
            "token1_address": info["token1_address"],
            # "fee": int(info["fee"]),
            "tick_spacing": int(info["tick_spacing"]),
            "called_block_number": info["called_block_number"],
            "sqrtPriceX96": pool_data["sqrtPriceX96"],
            "tick": pool_data["tick"],
            "block_number": block_number,
        }
        result.append(
            AllFeatureValueRecordUniswapV3Pool(
                feature_id=feature_id,
                block_number=block_number,
                address=address,
                value=value,
            )
        )
    return result


def get_exist_pools(db_service, nft_address):
    if not db_service:
        raise ValueError("uniswap v3 pool job must have db connection")

    session = db_service.get_service_session()
    try:
        result = (
            session.query(UniswapV3Pools).filter(UniswapV3Pools.nft_address == bytes.fromhex(nft_address[2:])).all()
        )
        history_pools = {}
        if result is not None:
            for item in result:
                pool_key = "0x" + item.pool_address.hex()
                history_pools[pool_key] = {
                    "pool_address": pool_key,
                    "token0_address": "0x" + item.token0_address.hex(),
                    "token1_address": "0x" + item.token1_address.hex(),
                    "fee": item.fee,
                    "tick_spacing": item.tick_spacing,
                    "called_block_number": item.called_block_number,
                }

    except Exception as e:
        print(e)
        raise e
    finally:
        session.close()

    return history_pools


def update_exist_pools(
    nft_address, factory_address, exist_pools, create_topic0, swap_topic0, logs, abi_list, web3, make_requests, is_batch
):
    need_add = {}
    swap_pools = []
    for log in logs:
        address = log.address
        if address in exist_pools:
            continue
        current_topic0 = log.topic0
        if factory_address == address and create_topic0 == current_topic0:
            decoded_data = decode_logs("PoolCreated", abi_list, log)
            pool_address = decoded_data["pool"]

            new_pool = {
                "nft_address": nft_address,
                "token0_address": decoded_data["token0"],
                "token1_address": decoded_data["token1"],
                "fee": decoded_data["fee"],
                "tick_spacing": decoded_data["tickSpacing"],
                "pool_address": pool_address,
                "called_block_number": log.block_number,
            }
            need_add[pool_address] = new_pool
        elif swap_topic0 == current_topic0:
            # if the address created by factory_address ,collect it
            swap_pools.append({"address": address, "block_number": log.block_number})
    swap_new_pools = collect_swap_new_pools(
        nft_address, factory_address, swap_pools, abi_list, web3, make_requests, is_batch
    )
    need_add.update(swap_new_pools)
    return need_add


def collect_pool_prices(target_topic0_list, exist_pools, logs, abi_list):
    pool_prices_map = {}
    for log in logs:
        address = log.address
        current_topic0 = log.topic0

        if address in exist_pools and current_topic0 in target_topic0_list:
            decoded_data = decode_logs("Swap", abi_list, log)
            pool_data = {
                "block_number": log.block_number,
                "log_index": log.log_index,
                "sqrtPriceX96": decoded_data["sqrtPriceX96"],
                "tick": decoded_data["tick"],
            }
            pool_prices_map[address] = pool_data

    return pool_prices_map


def collect_swap_new_pools(nft_address, factory_address, swap_pools, abi_list, web3, make_requests, is_batch):
    factory_infos = simple_get_rpc_requests(web3, make_requests, swap_pools, is_batch, abi_list, "factory", "address")
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
    token0_infos = simple_get_rpc_requests(web3, make_requests, uniswap_pools, is_batch, abi_list, "token0", "address")
    token1_infos = simple_get_rpc_requests(web3, make_requests, token0_infos, is_batch, abi_list, "token1", "address")
    tick_infos = simple_get_rpc_requests(
        web3, make_requests, token1_infos, is_batch, abi_list, "tickSpacing", "address"
    )
    # uniswap v3 pool have no fee function
    # fee_infos = simple_get_rpc_requests(web3, make_requests, tick_infos, is_batch, abi_list, "fee", "address")
    for data in tick_infos:
        pool_address = data["address"]
        new_pool = {
            "nft_address": nft_address,
            "token0_address": data["token0"],
            "token1_address": data["token1"],
            # "fee": data["fee"],
            "tick_spacing": data["tickSpacing"],
            "pool_address": pool_address,
            "called_block_number": data["block_number"],
        }
        need_add[pool_address] = new_pool
    return need_add


def simple_get_rpc_requests(web3, make_requests, requests, is_batch, abi_list, fn_name, contract_address_key):
    if len(requests) == 0:
        return []
    function_abi = next((abi for abi in abi_list if abi["name"] == fn_name and abi["type"] == "function"), None)
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    parameters = build_no_input_method_data(web3, requests, fn_name, abi_list, contract_address_key)

    token_name_rpc = list(generate_eth_call_json_rpc(parameters))
    if is_batch:
        response = make_requests(params=json.dumps(token_name_rpc))
    else:
        response = [make_requests(params=json.dumps(token_name_rpc[0]))]

    token_infos = []
    for data in list(zip_rpc_response(parameters, response)):
        result = rpc_response_to_result(data[1])
        token = data[0]
        value = result[2:] if result is not None else None
        try:
            decoded_data = eth_abi.decode(output_types, bytes.fromhex(value))
            token[fn_name] = decoded_data[0]

        except Exception as e:
            logger.error(
                f"Decoding {fn_name} failed. "
                f"token: {token}. "
                f"fn: {fn_name}. "
                f"rpc response: {result}. "
                f"exception: {e}"
            )
        token_infos.append(token)
    return token_infos


def decode_logs(fn_name, contract_abi, log):
    function_abi = next(
        (abi for abi in contract_abi if abi["name"] == fn_name and abi["type"] == "event"),
        None,
    )
    if not function_abi:
        raise ValueError("Function ABI not found")

    return decode_log(function_abi, log)
