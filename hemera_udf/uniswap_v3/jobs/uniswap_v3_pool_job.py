import logging

import hemera_udf.uniswap_v3.abi.aerodrome_abi as aerodrome_abi
import hemera_udf.uniswap_v3.abi.swapsicle_abi as swapsicle_abi
import hemera_udf.uniswap_v3.abi.uniswapv3_abi as uniswapv3_abi
from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.indexer.domains.log import Log
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import UniswapV3Pool
from hemera_udf.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from hemera_udf.uniswap_v3.util import AddressManager

logger = logging.getLogger(__name__)


class ExportUniSwapV3PoolJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [UniswapV3Pool]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = kwargs["config"].get("db_service")
        config = kwargs["config"]["uniswap_v3_job"]
        jobs = config.get("jobs", [])
        self._address_manager = AddressManager(jobs)
        # self._existing_pools = self.get_existing_pools()

    def get_filter(self):

        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    topics=[
                        abi_module.POOL_CREATED_EVENT.get_signature()
                        for abi_module in self._address_manager.abi_modules_list
                    ],
                    addresses=self._address_manager.factory_address_list,
                ),
            ]
        )

    def _process(self, **kwargs):
        self.get_pools()

    def get_pools(self):
        logs = self._data_buff[Log.type()]
        for log in logs:
            pool_dict = {}
            pool_address = None

            position_token_address = self._address_manager.get_position_by_factory(log.address)
            if log.topic0 == swapsicle_abi.POOL_CREATED_EVENT.get_signature():
                decoded_data = swapsicle_abi.POOL_CREATED_EVENT.decode_log(log)
                pool_address = decoded_data["pool"]
                # tick_spacing\fee are stored in other logs
                pool_dict.update(
                    {
                        "factory_address": log.address,
                        "position_token_address": position_token_address,
                        "token0_address": decoded_data["token0"],
                        "token1_address": decoded_data["token1"],
                        "pool_address": pool_address,
                        "block_number": log.block_number,
                        "block_timestamp": log.block_timestamp,
                        "fee": 0,
                        "tick_spacing": 0,
                    }
                )

            elif log.topic0 == uniswapv3_abi.POOL_CREATED_EVENT.get_signature():
                decoded_data = uniswapv3_abi.POOL_CREATED_EVENT.decode_log(log)
                pool_address = decoded_data["pool"]
                pool_dict.update(
                    {
                        "factory_address": log.address,
                        "position_token_address": position_token_address,
                        "token0_address": decoded_data["token0"],
                        "token1_address": decoded_data["token1"],
                        "fee": decoded_data["fee"],
                        "tick_spacing": decoded_data["tickSpacing"],
                        "pool_address": pool_address,
                        "block_number": log.block_number,
                        "block_timestamp": log.block_timestamp,
                    }
                )

            elif log.topic0 == aerodrome_abi.POOL_CREATED_EVENT.get_signature():
                decoded_data = aerodrome_abi.POOL_CREATED_EVENT.decode_log(log)
                pool_address = decoded_data["pool"]
                pool_dict.update(
                    {
                        "factory_address": log.address,
                        "position_token_address": position_token_address,
                        "token0_address": decoded_data["token0"],
                        "token1_address": decoded_data["token1"],
                        "fee": 0,
                        "tick_spacing": decoded_data["tickSpacing"],
                        "pool_address": pool_address,
                        "block_number": log.block_number,
                        "block_timestamp": log.block_timestamp,
                    }
                )

            if pool_address and position_token_address:
                # self._existing_pools.add(pool_address)
                uniswap_v3_pool = UniswapV3Pool(**pool_dict)
                self._collect_domain(uniswap_v3_pool)

    def get_existing_pools(self):
        session = self._service.Session()
        try:
            existing_pools = set()
            pools_orm = session.query(UniswapV3Pools).all()
            for pool in pools_orm:
                existing_pools.add(bytes_to_hex_str(pool.pool_address))

        except Exception as e:
            print(e)
            raise e
        finally:
            session.close()

        return existing_pools
