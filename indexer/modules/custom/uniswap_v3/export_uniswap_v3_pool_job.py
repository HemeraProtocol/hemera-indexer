import configparser
import json
import logging
import os
import threading
from collections import defaultdict

import eth_abi

from common import models

from indexer.domain import dict_to_dataclass
from indexer.modules.custom.uniswap_v3.domain.all_features_value_record import AllFeatureValueRecord
from indexer.modules.custom.uniswap_v3.domain.feature_uniswap_v3 import UniswapV3Pool
from indexer.domain.log import Log
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.uniswap_v3.util import load_abi
from indexer.specification.specification import TransactionFilterByLogs, TopicSpecification

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.UNISWAP_V3_POOLS.value


class ExportUniSwapV3PoolJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [AllFeatureValueRecord, UniswapV3Pool]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs['batch_size'], kwargs['max_workers'],
            job_name=self.__class__.__name__
        )
        self._is_batch = kwargs['batch_size'] > 1
        self._service = kwargs['config'].get('db_service'),
        self._new_pools = {}
        self._pool_prices = {}
        self._pool_prices_lock = threading.Lock()
        self._load_config('config.ini')
        self._abi_list = load_abi('abi.json')
        self._exist_pools = get_exist_pools(self._service[0], self._nft_address)

    def get_filter(self):
        return TransactionFilterByLogs([
            TopicSpecification(addresses=[self._factory_address], topics=[self._create_pool_topic0]),
            TopicSpecification(topics=[self._pool_swap_topic0])
        ])

    def _load_config(self, filename):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)

        try:
            self._nft_address = config.get('info', 'nft_address').lower()
            self._factory_address = config.get('info', 'factory_address').lower()
            self._create_pool_topic0 = config.get('info', 'create_pool_topic0').lower()
            self._pool_swap_topic0 = config.get('info', 'pool_swap_topic0').lower()
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def _start(self):
        super()._start()

    def _collect(self, **kwargs):
        logs = self._data_buff[Log.type()]
        grouped_logs = defaultdict(dict)
        for log in logs:
            key = (log.address, log.topic0, log.block_number)
            if key not in grouped_logs or log.log_index > grouped_logs[key].log_index:
                grouped_logs[key] = log

        max_log_index_records = list(grouped_logs.values())
        self._batch_work_executor.execute(max_log_index_records,
                                          self._collect_batch,
                                          len(max_log_index_records))
        self._batch_work_executor.wait()

    def _collect_batch(self, logs):
        # first collect pool info
        need_add_in_exists_pools = update_exist_pools(self._nft_address, self._factory_address,
                                                      self._create_pool_topic0,
                                                      logs, self._abi_list)
        self._new_pools.update(need_add_in_exists_pools)

        self._exist_pools.update(need_add_in_exists_pools)

        pool_prices = collect_pool_prices([self._pool_swap_topic0], self._exist_pools, logs, self._abi_list)
        self.update_pool_prices(pool_prices)

        for pools in format_pool_item(need_add_in_exists_pools):
            self._collect_item(UniswapV3Pool.type(), pools)

        for record in format_value_records(self._exist_pools, pool_prices, FEATURE_ID):
            self._collect_item(AllFeatureValueRecord.type(), record)

    def _process(self):
        self._data_buff[UniswapV3Pool.type()].sort(key=lambda x: x.mint_block_number)
        self._data_buff[AllFeatureValueRecord.type()].sort(key=lambda x: x.block_number)

    def update_pool_prices(self, new_pool_prices):
        if not new_pool_prices or len(new_pool_prices) == 0:
            return
        with self._pool_prices_lock:
            for address, new_data in new_pool_prices.items():
                if address in self._pool_prices:
                    current_data = self._pool_prices[address]
                    if (new_data['block_number'] > current_data['block_number'] or
                            (new_data['block_number'] == current_data['block_number'] and
                             new_data['log_index'] > current_data['log_index'])):
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
        block_number = pool_data['block_number']
        value = {
            'token0_address': info['token0_address'],
            'token1_address': info['token1_address'],
            'fee': int(info['fee']),
            'tick_spacing': int(info['tick_spacing']),
            'mint_block_number': info['mint_block_number'],
            'sqrtPriceX96': pool_data['sqrtPriceX96'],
            'tick': pool_data['tick'],
            'block_number': block_number
        }
        result.append(
            AllFeatureValueRecord(
                feature_id=feature_id,
                block_number=block_number,
                address=address,
                value=value,
            )
        )
    return result


def get_exist_pools(db_service, nft_address):
    if not db_service:
        raise ValueError('uniswap v3 pool job must have db connection')

    session = db_service.get_service_session()
    try:
        result = session.query(models.UniswapV3Pools) \
            .filter(
            models.UniswapV3Pools.nft_address == bytes.fromhex(nft_address[2:])).all()
        history_pools = {}
        if result is not None:
            for item in result:
                pool_key = '0x' + item.pool_address.hex()
                history_pools[pool_key] = {
                    'pool_address': pool_key,
                    'token0_address': '0x' + item.token0_address.hex(),
                    'token1_address': '0x' + item.token1_address.hex(),
                    'fee': item.fee,
                    'tick_spacing': item.tick_spacing,
                    'mint_block_number': item.mint_block_number
                }

    except Exception as e:
        print(e)
        raise e
    finally:
        session.close()

    return history_pools


def update_exist_pools(nft_address, factory_address, target_topic0, logs, abi_list):
    need_add = {}
    for log in logs:
        address = log.address
        current_topic0 = log.topic0
        if factory_address == address and target_topic0 == current_topic0:
            decoded_data = decode_logs('PoolCreated', abi_list, log.topic1, log.topic2, log.topic3,
                                       log.data)
            pool_address = decoded_data[4]

            new_pool = {
                'nft_address': nft_address,
                'token0_address': decoded_data[0],
                'token1_address': decoded_data[1],
                'fee': decoded_data[2],
                'tick_spacing': decoded_data[3],
                'pool_address': pool_address,
                'mint_block_number': log.block_number
            }
            need_add[pool_address] = new_pool

    return need_add


def collect_pool_prices(target_topic0_list, exist_pools, logs, abi_list):
    pool_prices_map = {}
    for log in logs:
        address = log.address
        current_topic0 = log.topic0

        if address in exist_pools and current_topic0 in target_topic0_list:
            decoded_data = decode_logs('Swap', abi_list, log.topic1, log.topic2, log.topic3,
                                       log.data)
            pool_data = {
                'block_number': log.block_number,
                'log_index': log.log_index,
                'sqrtPriceX96': decoded_data[4],
                'tick': decoded_data[6],
            }
            pool_prices_map[address] = pool_data

    return pool_prices_map


def decode_logs(fn_name, contract_abi, topic1, topic2, topic3, data):
    function_abi = next((abi for abi in contract_abi if abi['name'] == fn_name and abi['type'] == 'event'), None)
    if not function_abi:
        raise ValueError("Function ABI not found")

    indexed_inputs = [input for input in function_abi['inputs'] if input.get('indexed', False)]
    non_indexed_inputs = [input for input in function_abi['inputs'] if not input.get('indexed', False)]

    input_types = [input['type'] for input in indexed_inputs + non_indexed_inputs]

    encode_data = encode_data_together(topic1, topic2, topic3, data)

    decoded_data = eth_abi.decode(input_types, bytes.fromhex(encode_data))

    return decoded_data


def encode_data_together(topic1, topic2, topic3, data):
    encode_data = ''
    topics = [topic1, topic2, topic3, data]

    for topic in topics:
        if topic is not None:
            if isinstance(topic, str) and topic.startswith('0x'):
                encode_data += topic[2:]
            else:
                encode_data += str(topic)
    return encode_data
