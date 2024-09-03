import configparser
import json
import logging
import os

from indexer.domain.log import Log
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.uniswap_v3.domain.feature_uniswap_v3 import UniswapV3Pool
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from web3 import Web3

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.UNISWAP_V3_POOLS.value


class UniSwapV3FindPoolJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [UniswapV3Pool]
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
        self._batch_size = kwargs["batch_size"]
        self._max_worker = kwargs["max_workers"]

    def get_filter(self):
        return TransactionFilterByLogs(
            [TopicSpecification(addresses=[self._factory_address], topics=[self._create_pool_topic0])])

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
            self._pool_swap_topic0 = chain_config.get("pool_swap_topic0").lower()
            self._liquidity_topic0_dict = json.loads(chain_config.get("liquidity_topic0_dict", "{}"))
            topic0_list_str = chain_config.get("liquidity_nft_topic0_list")
            self._liquidity_nft_topic0_list = [address.strip() for address in topic0_list_str.split(",") if
                                               address.strip()]
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        self._batch_work_executor.execute(logs, self._collect_batch, len(logs))
        self._batch_work_executor.wait()

    def _collect_batch(self, logs):
        for log in logs:
            address = log.address
            current_topic0 = log.topic0
            if self._factory_address != address or self._create_pool_topic0 != current_topic0:
                continue
            entity = decode_pool_created(self._nft_address, self._factory_address, log)
            self._collect_item(UniswapV3Pool.type(), entity)

    def _process(self, **kwargs):
        self._data_buff[UniswapV3Pool.type()].sort(key=lambda x: x.block_number)


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
