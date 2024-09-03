import configparser
import json
import logging
import os
from collections import defaultdict
import eth_abi

from indexer.domain.log import Log
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.uniswap_v3.constants import UNISWAP_V3_ABI
from indexer.modules.custom.uniswap_v3.domain.feature_uniswap_v3 import UniswapV3Pool, UniswapV3PoolPrice, \
    UniswapV3PoolCurrentPrice
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from web3 import Web3

from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.utils import zip_rpc_response, rpc_response_to_result

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.UNISWAP_V3_POOLS.value


class UniSwapV3FindPoolJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [UniswapV3Pool, UniswapV3PoolPrice, UniswapV3PoolCurrentPrice]
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
        self._chain_id = common_utils.get_chain_id(self._web3)
        self._load_config("config.ini", self._chain_id)
        self._exist_pools = get_exist_pools(self._service, self._nft_address)
        self._batch_size = kwargs["batch_size"]
        self._max_worker = kwargs["max_workers"]
        self._abi_list = UNISWAP_V3_ABI

    def get_filter(self):
        return TransactionFilterByLogs(
            [TopicSpecification(addresses=[self._factory_address], topics=[self._create_pool_topic0]),
             TopicSpecification(topics=self._pool_price_topic0_list)])

    def _load_config(self, filename, chain_id):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)
        chain_id_str = str(chain_id)
        try:
            chain_config = config[chain_id_str]
        except KeyError:
            return
        try:
            self._nft_address = chain_config.get("nft_address").lower()
            self._factory_address = chain_config.get("factory_address").lower()
            self._create_pool_topic0 = chain_config.get("create_pool_topic0").lower()
            topic0_list_str = chain_config.get("pool_price_topic0_list")
            self._pool_price_topic0_list = [topic0.strip() for topic0 in topic0_list_str.split(",") if topic0.strip()]
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        self._batch_work_executor.execute(logs, self._collect_pool_batch, len(logs))
        self._batch_work_executor.wait()

        collected_pools = self._data_buff[UniswapV3Pool.type()]
        for data in collected_pools:
            self._exist_pools.add(data.pool_address)
        self._batch_work_executor.execute(logs, self._collect_price_batch, len(logs), split_logs)
        self._batch_work_executor.wait()

    def _collect_pool_batch(self, logs):
        for log in logs:
            address = log.address
            current_topic0 = log.topic0
            if self._factory_address != address or self._create_pool_topic0 != current_topic0:
                continue
            entity = decode_pool_created(self._nft_address, self._factory_address, log)
            self._collect_item(UniswapV3Pool.type(), entity)

    def _collect_price_batch(self, logs_dict):
        if not logs_dict:
            return

        contract_address = next(iter(logs_dict))
        if contract_address not in self._exist_pools:
            return
        logs = logs_dict[contract_address]
        unique_logs = set()
        for log in logs:
            log_tuple = (log.address, log.block_number, log.block_timestamp)
            unique_logs.add(log_tuple)
        requests = [
            {"pool_address": address, "block_number": block_number, "block_timestamp": block_timestamp}
            for address, block_number, block_timestamp in unique_logs
        ]
        pool_prices = slot0_rpc_requests(self._web3, self._batch_web3_provider.make_request, requests, self._is_batch,
                                         self._abi_list, self._batch_size, self._max_worker)
        current_price = None
        for data in pool_prices:
            pool_data = {
                "sqrtPriceX96": data["sqrtPriceX96"],
                "tick": data["tick"],
                "block_number": data["block_number"],
            }

    def _process(self, **kwargs):
        self._data_buff[UniswapV3Pool.type()].sort(key=lambda x: x.block_number)
        self._data_buff[UniswapV3PoolPrice.type()].sort(key=lambda x: x.block_number)
        self._data_buff[UniswapV3PoolCurrentPrice.type()].sort(key=lambda x: x.block_number)


def decode_pool_created(nft_address, factory_address, log):
    token0_address = parse_hex_to_address(log.topic1)
    token1_address = parse_hex_to_address(log.topic2)
    fee = parse_hex_to_uint256(log.topic3)
    tick_hex, pool_hex = split_hex_string(log.data)
    pool_address = parse_hex_to_address(pool_hex)
    tick_spacing = parse_hex_to_uint256(tick_hex)
    return UniswapV3Pool(nft_address=nft_address, factory_address=factory_address, pool_address=pool_address,
                         token0_address=token0_address, token1_address=token1_address,
                         fee=fee, tick_spacing=tick_spacing,
                         block_number=log.block_number, block_timestamp=log.block_timestamp)


def parse_hex_to_address(hex_string):
    hex_string = hex_string.lower().replace('0x', '')

    if len(hex_string) > 40:
        hex_string = hex_string[-40:]

    hex_string = hex_string.zfill(40)
    return Web3.to_checksum_address(hex_string).lower()


def parse_hex_to_uint256(hex_string):
    return Web3.to_int(hexstr=hex_string)


def split_hex_string(hex_string):
    if hex_string.startswith("0x"):
        hex_string = hex_string[2:]

    if len(hex_string) == 128:
        part1 = hex_string[:64]
        part2 = hex_string[64:]
        return part1, part2
    else:
        raise ValueError("The data is not belong to Uniswap-V3 Factory")


def get_exist_pools(db_service, nft_address):
    if not db_service:
        return {}

    session = db_service.get_service_session()
    try:
        result = (
            session.query(UniswapV3Pools).filter(UniswapV3Pools.nft_address == bytes.fromhex(nft_address[2:])).all()
        )
        history_pools = set()
        if result is not None:
            for item in result:
                pool_key = "0x" + item.pool_address.hex()
                history_pools.add(pool_key)
    except Exception as e:
        raise e
    finally:
        session.close()

    return history_pools


def split_logs(logs):
    log_dict = defaultdict(list)
    for data in logs:
        log_dict[data.address].append(data)

    for contract_address, data in log_dict.items():
        yield {contract_address: data}


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
