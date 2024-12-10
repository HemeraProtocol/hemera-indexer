import logging

from indexer.domain.log import Log
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.uniswap_v2.aerodrome_abi import POOL_CREATED_EVENT
from indexer.modules.custom.uniswap_v2.domain.feature_uniswap_v2 import UniswapV2Pool
from indexer.modules.custom.uniswap_v2.uniswapv2_abi import PAIR_CREATED_EVENT
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportUniSwapV2PoolJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [UniswapV2Pool]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(topics=[PAIR_CREATED_EVENT.get_signature(), POOL_CREATED_EVENT.get_signature()]),
            ]
        )

    def _process(self, **kwargs):
        logs = self._data_buff[Log.type()]
        for log in logs:
            pool = None

            if log.topic0 == PAIR_CREATED_EVENT.get_signature():
                decoded_dict = PAIR_CREATED_EVENT.decode_log(log)
                pool = UniswapV2Pool(
                    factory_address=log.address,
                    pool_address=decoded_dict["pair"],
                    token0_address=decoded_dict["token0"],
                    token1_address=decoded_dict["token1"],
                    length=decoded_dict[""],
                    block_number=log.block_number,
                    block_timestamp=log.block_timestamp,
                )
            elif log.topic0 == POOL_CREATED_EVENT.get_signature():
                decoded_dict = POOL_CREATED_EVENT.decode_log(log)
                pool = UniswapV2Pool(
                    factory_address=log.address,
                    pool_address=decoded_dict["pool"],
                    token0_address=decoded_dict["token0"],
                    token1_address=decoded_dict["token1"],
                    length=decoded_dict[""],
                    block_number=log.block_number,
                    block_timestamp=log.block_timestamp,
                )

            if pool:
                self._collect_domain(pool)
