import configparser
import json
import logging
import os
import threading
from collections import defaultdict

import eth_abi

from hemera.common.utils.abi_code_utils import decode_log
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from hemera.indexer.domain import dict_to_dataclass
from hemera.indexer.domain.log import Log
from hemera.indexer.executors.batch_work_executor import BatchWorkExecutor
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.modules.custom.all_features_value_record import AllFeatureValueRecordUniswapV2Info
from hemera.indexer.modules.custom.feature_type import FeatureType
from hemera.indexer.modules.custom.uniswap_v2.constants import UNISWAP_V2_ABI, ThreadSafeList
from hemera.indexer.modules.custom.uniswap_v2.domain.feature_uniswap_v2 import UniswapV2Pool
from hemera.indexer.modules.custom.uniswap_v2.models.feature_uniswap_v2_pools import UniswapV2Pools
from hemera.indexer.modules.custom.uniswap_v3.util import build_no_input_method_data
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from hemera.indexer.utils.rpc_utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.UNISWAP_V2_INFO.value


class ExportUniSwapV2InfoJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [AllFeatureValueRecordUniswapV2Info, UniswapV2Pool]

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
        self._abi_list = UNISWAP_V2_ABI
        self._exist_pools = get_exist_pools(self._service[0], self._factory_address)
        self._collected_total_supply = ThreadSafeList()

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=[self._factory_address], topics=[self._create_pool_topic0]),
                TopicSpecification(topics=[self._pool_mint_topic0, self._pool_burn_topic0]),
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
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        grouped_logs = defaultdict(dict)
        for log in logs:
            key = (log.address, log.topic0, log.block_number)
            if key not in grouped_logs or log.log_index > grouped_logs[key].log_index:
                grouped_logs[key] = log
        max_log_index_records = list(grouped_logs.values())

        # first collect pool info
        need_add_in_exists_pools = update_exist_pools(
            self._factory_address,
            self._exist_pools,
            self._create_pool_topic0,
            self._pool_mint_topic0,
            self._pool_burn_topic0,
            max_log_index_records,
            self._abi_list,
            self._web3,
            self._batch_web3_provider.make_request,
            self._is_batch,
        )
        self._exist_pools.update(need_add_in_exists_pools)

        for pools in format_pool_item(need_add_in_exists_pools):
            self._collect_item(UniswapV2Pool.type(), pools)

        self._batch_work_executor.execute(max_log_index_records, self._collect_batch, len(max_log_index_records))
        self._batch_work_executor.wait()

    def _collect_batch(self, logs):

        pool_total_supply = collect_pool_total_supply(
            [self._pool_mint_topic0, self._pool_burn_topic0],
            self._exist_pools,
            logs,
            self._abi_list,
            self._web3,
            self._batch_web3_provider.make_request,
            self._is_batch,
        )
        self._collected_total_supply.add_items(pool_total_supply)

    def _process(self, **kwargs):

        for record in format_value_records(self._exist_pools, self._collected_total_supply, FEATURE_ID):
            self._collect_item(AllFeatureValueRecordUniswapV2Info.type(), record)

        self._data_buff[UniswapV2Pool.type()].sort(key=lambda x: x.called_block_number)
        self._data_buff[AllFeatureValueRecordUniswapV2Info.type()].sort(key=lambda x: x.block_number)
        self._collected_total_supply.clear_list()


def add_list_to_queue(queue, items):
    for item in items:
        queue.put(item)


def format_pool_item(new_pools):
    result = []
    for pool_address, pool in new_pools.items():
        result.append(dict_to_dataclass(pool, UniswapV2Pool))
    return result


def format_value_records(exist_pools, pool_total_supply, feature_id):
    result = []
    help_set = set()
    for data in pool_total_supply:
        address = data["address"]
        block_number = data["block_number"]
        total_supply = data["total_supply"]
        key = (address, block_number)
        if address not in exist_pools.keys() or key in help_set:
            continue
        help_set.add(key)
        info = exist_pools.get(address)
        pass
        value = {
            "token0_address": info["token0_address"],
            "token1_address": info["token1_address"],
            "total_supply": total_supply,
            "block_number": block_number,
        }
        result.append(
            AllFeatureValueRecordUniswapV2Info(
                feature_id=feature_id,
                block_number=block_number,
                address=address,
                value=value,
            )
        )
    return result


def get_exist_pools(db_service, factory_address):
    if not db_service:
        raise ValueError("uniswap v2 pool job must have db connection")

    session = db_service.get_service_session()
    try:
        result = (
            session.query(UniswapV2Pools)
            .filter(UniswapV2Pools.factory_address == hex_str_to_bytes(factory_address))
            .all()
        )
        history_pools = {}
        if result is not None:
            for item in result:
                pool_key = bytes_to_hex_str(item.pool_address)
                history_pools[pool_key] = {
                    "pool_address": pool_key,
                    "token0_address": bytes_to_hex_str(item.token0_address),
                    "token1_address": bytes_to_hex_str(item.token1_address),
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
    factory_address, exist_pools, create_topic0, mint_topic0, burn_topic0, logs, abi_list, web3, make_requests, is_batch
):
    need_add = {}
    active_pools = []
    for log in logs:
        address = log.address
        if address in exist_pools:
            continue
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
            # if the address created by factory_address ,collect it
            active_pools.append({"address": address, "block_number": log.block_number})
    swap_new_pools = collect_active_new_pools(factory_address, active_pools, abi_list, web3, make_requests, is_batch)
    need_add.update(swap_new_pools)
    return need_add


def collect_pool_total_supply(target_topic0_list, exist_pools, logs, abi_list, web3, make_requests, is_batch):
    need_collect = {}

    for log in logs:
        if log.topic0 in target_topic0_list and log.address in exist_pools.keys():
            key = (log.address, log.block_number)

            need_collect[key] = {"address": log.address, "block_number": log.block_number}

    need_collect_list = list(need_collect.values())
    # call totalSupply
    total_supply_infos = simple_get_rpc_requests(
        web3, make_requests, need_collect_list, is_batch, abi_list, "totalSupply", "address"
    )
    result = []
    for data in total_supply_infos:
        address = data["address"]
        block_number = data["block_number"]
        total_supply = data["totalSupply"]

        result.append(
            {
                "address": address,
                "block_number": block_number,
                "total_supply": total_supply,
            }
        )
    return result


def collect_active_new_pools(factory_address, active_pools, abi_list, web3, make_requests, is_batch):
    factory_infos = simple_get_rpc_requests(web3, make_requests, active_pools, is_batch, abi_list, "factory", "address")
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
