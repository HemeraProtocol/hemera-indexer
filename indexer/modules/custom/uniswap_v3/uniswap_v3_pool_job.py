import logging

from common.utils.format_utils import bytes_to_hex_str
from indexer.domain.transaction import Transaction
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.uniswap_v3.domains.feature_uniswap_v3 import (
    UniswapV3Pool,
)
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from indexer.modules.custom.uniswap_v3.swapsicle_abi import POOL_EVENT
from indexer.modules.custom.uniswap_v3.uniswapv3_abi import (
    POOL_CREATED_EVENT,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportUniSwapV3PoolJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [UniswapV3Pool]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = kwargs["config"].get("db_service")
        # config = kwargs["config"]["uniswap_v3_pool_job"]
        # self._position_token_address = config.get("position_token_address").lower()
        # self._factory_address = config.get("factory_address").lower()
        self._existing_pools = self.get_existing_pools()

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    topics=[
                        # POOL EVENT
                        # POOL_CREATED_EVENT.get_signature(),
                        POOL_EVENT.get_signature()
                    ]
                ),
            ]
        )

    def _process(self, **kwargs):
        self.get_swapsicle_pools()
        self.get_uniswapv3_pools()

    def get_swapsicle_pools(self):
        transactions = self._data_buff['transaction']
        for transaction in transactions:
            logs = transaction.receipt.logs
            pool_dict = {}
            for log in logs:
                if log.topic0 == POOL_EVENT.get_signature():
                    decoded_data = POOL_EVENT.decode_log(log)
                    pool_address = decoded_data["pool"]
                    # tick_spacing\fee are stored in other logs
                    pool_dict.update({
                        'factory_address': log.address,
                        'position_token_address': transaction.to_address,
                        "token0_address": decoded_data["token0"],
                        "token1_address": decoded_data["token1"],
                        "pool_address": pool_address,
                        "block_number": log.block_number,
                        "block_timestamp": log.block_timestamp,
                        "fee": 0,
                        "tick_spacing": 0,
                    })
                    if pool_address not in self._existing_pools:
                        self._existing_pools.append(pool_address)
                        uniswap_v3_pool = UniswapV3Pool(**pool_dict)
                        self._collect_domain(uniswap_v3_pool)

    def get_uniswapv3_pools(self):
        transactions = self._data_buff['transaction']
        for transaction in transactions:
            logs = transaction.receipt.logs
            pool_dict = {}
            for log in logs:
                if log.topic0 == POOL_CREATED_EVENT.get_signature():
                    decoded_data = POOL_CREATED_EVENT.decode_log(log)
                    pool_address = decoded_data["pool"]
                    pool_dict.update({
                        'factory_address': log.address,
                        'position_token_address': transaction.to_address,
                        "token0_address": decoded_data["token0"],
                        "token1_address": decoded_data["token1"],
                        "fee": decoded_data["fee"],
                        "tick_spacing": decoded_data["tickSpacing"],
                        "pool_address": pool_address,
                        "block_number": log.block_number,
                        "block_timestamp": log.block_timestamp,
                    })
                    if pool_address not in self._existing_pools:
                        self._existing_pools.append(pool_address)
                        uniswap_v3_pool = UniswapV3Pool(**pool_dict)
                        self._collect_domain(uniswap_v3_pool)

    def get_existing_pools(self):
        session = self._service.Session()
        try:
            pools_orm = (
                session.query(UniswapV3Pools)
                .all()
            )
            existing_pools = [bytes_to_hex_str(p.pool_address) for p in pools_orm]

        except Exception as e:
            print(e)
            raise e
        finally:
            session.close()

        return existing_pools
