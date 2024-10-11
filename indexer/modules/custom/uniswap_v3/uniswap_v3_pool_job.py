import configparser
import json
import logging
import os
from dataclasses import fields
from itertools import groupby
from operator import attrgetter

from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.uniswap_v3 import constants, util
from indexer.modules.custom.uniswap_v3.constants import UNISWAP_V3_ABI
from indexer.modules.custom.uniswap_v3.domain.feature_uniswap_v3 import (
    UniswapV3Pool,
    UniswapV3PoolCurrentPrice,
    UniswapV3PoolPrice,
    UniswapV3SwapEvent,
)
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.rpc_utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.UNISWAP_V3_POOLS.value


class UniSwapV3PoolJob(FilterTransactionDataJob):
    dependency_types = [Transaction, Log]
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
        self._chain_id = common_utils.get_chain_id(self._web3)
        self._load_config("config.ini", self._chain_id)
        self._exist_pools = get_exist_pools(self._service, self._position_token_address)
        self._batch_size = kwargs["batch_size"]
        self._max_worker = kwargs["max_workers"]
        self._abi_list = UNISWAP_V3_ABI
        self._create_pool_topic0 = constants.UNISWAP_V3_CREATE_POOL_TOPIC0
        self._pool_price_topic0_list = constants.UNISWAP_V3_POOL_PRICE_TOPIC0_LIST

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=[self._factory_address], topics=[self._create_pool_topic0]),
                TopicSpecification(topics=self._pool_price_topic0_list),
            ]
        )

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
            self._position_token_address = chain_config.get("nft_address").lower()
            self._factory_address = chain_config.get("factory_address").lower()
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        self._batch_work_executor.execute(logs, self._collect_pool_batch, len(logs))
        self._batch_work_executor.wait()

        collected_pools = self._data_buff[UniswapV3Pool.type()]
        for data in collected_pools:
            self._exist_pools[data.pool_address] = data
        transactions = self._data_buff[Transaction.type()]
        self._transaction_hash_from_dict = {}
        for transaction in transactions:
            self._transaction_hash_from_dict[transaction.hash] = transaction.from_address
        self._batch_work_executor.execute(logs, self._collect_price_batch, len(logs))
        self._batch_work_executor.wait()
        self._transaction_hash_from_dict = {}
        self._process_current_pool_prices()

    def _collect_pool_batch(self, logs):
        for log in logs:
            address = log.address
            current_topic0 = log.topic0
            if self._factory_address != address or self._create_pool_topic0 != current_topic0:
                continue
            entity = decode_pool_created(self._position_token_address, self._factory_address, log)
            self._collect_item(UniswapV3Pool.type(), entity)

    def _collect_price_batch(self, logs):
        unique_logs = set()
        for log in logs:
            if log.address not in self._exist_pools:
                continue
            # Collect swap logs
            if log.topic0 == constants.UNISWAP_V3_POOL_SWAP_TOPIC0:
                transaction_hash = log.transaction_hash
                part1, part2, part3, part4, part5 = split_swap_data_hex_string(log.data)
                amount0 = util.parse_hex_to_int256(part1)
                amount1 = util.parse_hex_to_int256(part2)
                sqrt_price_x96 = util.parse_hex_to_int256(part3)
                liquidity = util.parse_hex_to_int256(part4)
                tick = util.parse_hex_to_int256(part5)
                pool_data = self._exist_pools[log.address]
                self._collect_item(
                    UniswapV3SwapEvent.type(),
                    UniswapV3SwapEvent(
                        pool_address=log.address,
                        position_token_address=self._position_token_address,
                        transaction_hash=transaction_hash,
                        transaction_from_address=self._transaction_hash_from_dict[transaction_hash],
                        log_index=log.log_index,
                        block_number=log.block_number,
                        block_timestamp=log.block_timestamp,
                        sender=util.parse_hex_to_address(log.topic1),
                        recipient=util.parse_hex_to_address(log.topic2),
                        amount0=amount0,
                        amount1=amount1,
                        liquidity=liquidity,
                        tick=tick,
                        sqrt_price_x96=sqrt_price_x96,
                        token0_address=pool_data.token0_address,
                        token1_address=pool_data.token1_address,
                    ),
                )
            log_tuple = (log.address, log.block_number, log.block_timestamp)
            unique_logs.add(log_tuple)
        requests = [
            {"pool_address": address, "block_number": block_number, "block_timestamp": block_timestamp}
            for address, block_number, block_timestamp in unique_logs
        ]
        pool_prices = slot0_rpc_requests(
            self._web3,
            self._batch_web3_provider.make_request,
            requests,
            self._is_batch,
            self._abi_list,
            self._batch_size,
            self._max_worker,
        )
        for data in pool_prices:
            detail = UniswapV3PoolPrice(
                factory_address=self._factory_address,
                pool_address=data["pool_address"],
                sqrt_price_x96=data["sqrtPriceX96"],
                tick=data["tick"],
                block_number=data["block_number"],
                block_timestamp=data["block_timestamp"],
            )
            self._collect_item(UniswapV3PoolPrice.type(), detail)

    def _process(self, **kwargs):
        self._data_buff[UniswapV3Pool.type()].sort(key=lambda x: x.block_number)
        self._data_buff[UniswapV3PoolPrice.type()].sort(key=lambda x: x.block_number)
        self._data_buff[UniswapV3PoolCurrentPrice.type()].sort(key=lambda x: x.block_number)
        self._data_buff[UniswapV3SwapEvent.type()].sort(key=lambda x: x.block_number)

    def _process_current_pool_prices(self):
        prices = self._data_buff[UniswapV3PoolPrice.type()]
        self._data_buff[UniswapV3PoolPrice.type()] = []
        unique_prices = {}
        for price in prices:
            key = (price.pool_address, price.block_number)
            unique_prices[key] = price

        for price in unique_prices.values():
            self._collect_item(UniswapV3PoolPrice.type(), price)

        sorted_prices = sorted(unique_prices.values(), key=lambda x: (x.pool_address, x.block_number))
        current_prices = [
            max(group, key=attrgetter("block_number"))
            for _, group in groupby(sorted_prices, key=attrgetter("pool_address"))
        ]
        for data in current_prices:
            self._collect_item(UniswapV3PoolCurrentPrice.type(), self.create_current_price_status(data))

    @staticmethod
    def create_current_price_status(detail: UniswapV3PoolPrice) -> UniswapV3PoolCurrentPrice:
        return UniswapV3PoolCurrentPrice(
            **{field.name: getattr(detail, field.name) for field in fields(UniswapV3PoolPrice)}
        )


def decode_pool_created(position_token_address, factory_address, log):
    token0_address = util.parse_hex_to_address(log.topic1)
    token1_address = util.parse_hex_to_address(log.topic2)
    fee = util.parse_hex_to_int256(log.topic3)
    tick_hex, pool_hex = split_hex_string(log.data)
    pool_address = util.parse_hex_to_address(pool_hex)
    tick_spacing = util.parse_hex_to_int256(tick_hex)
    return UniswapV3Pool(
        position_token_address=position_token_address,
        factory_address=factory_address,
        pool_address=pool_address,
        token0_address=token0_address,
        token1_address=token1_address,
        fee=fee,
        tick_spacing=tick_spacing,
        block_number=log.block_number,
        block_timestamp=log.block_timestamp,
    )


def split_hex_string(hex_string):
    if hex_string.startswith("0x"):
        hex_string = hex_string[2:]

    if len(hex_string) == 128:
        part1 = hex_string[:64]
        part2 = hex_string[64:]
        return part1, part2
    else:
        raise ValueError("The data is not belong to Uniswap-V3 Factory")


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
                history_pools[pool_key] = UniswapV3Pool(
                    position_token_address=bytes_to_hex_str(item.position_token_address),
                    pool_address=pool_key,
                    token0_address=bytes_to_hex_str(item.token0_address),
                    token1_address=bytes_to_hex_str(item.token1_address),
                    factory_address=bytes_to_hex_str(item.factory_address),
                    fee=item.fee,
                    tick_spacing=item.tick_spacing,
                    block_number=item.block_number,
                    block_timestamp=item.block_timestamp,
                )
    except Exception as e:
        raise e
    finally:
        session.close()

    return history_pools


def slot0_rpc_requests(web3, make_requests, requests, is_batch, abi_list, batch_size, max_worker):
    if len(requests) == 0:
        return []
    fn_name = "slot0"
    function_abi = next((abi for abi in abi_list if abi["name"] == fn_name and abi["type"] == "function"), None)
    outputs = function_abi["outputs"]
    output_types = [output["type"] for output in outputs]

    parameters = common_utils.build_no_input_method_data(web3, requests, fn_name, abi_list)
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
            part1, part2 = get_price_and_tick_from_hex(value)
            pool["sqrtPriceX96"] = part1
            pool["tick"] = part2
        except Exception as e:
            logger.error(f"Decoding {fn_name} failed. " f"rpc response: {result}. " f"exception: {e}")
        token_infos.append(pool)
    return token_infos


def get_price_and_tick_from_hex(hex_string):
    if hex_string.startswith("0x"):
        hex_string = hex_string[2:]
    part1 = hex_string[:64]
    part2 = hex_string[64:128]
    return util.parse_hex_to_int256(part1), util.parse_hex_to_int256(part2)


def split_swap_data_hex_string(hex_string):
    if hex_string.startswith("0x"):
        hex_string = hex_string[2:]
    if len(hex_string) == 320:
        part1 = hex_string[:64]
        part2 = hex_string[64:128]
        part3 = hex_string[128:192]
        part4 = hex_string[192:256]
        part5 = hex_string[256:]
        return part1, part2, part3, part4, part5
    else:
        raise ValueError("The data length is not suitable for this operation.")
