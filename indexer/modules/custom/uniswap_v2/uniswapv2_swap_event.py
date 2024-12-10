import logging

from indexer.domain.log import Log
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.uniswap_v2.aerodrome_abi import SWAP_EVENT as AERODROME_SWAP_EVENT
from indexer.modules.custom.uniswap_v2.domain.feature_uniswap_v2 import UniswapV2SwapEvent
from indexer.modules.custom.uniswap_v2.uniswapv2_abi import SWAP_EVENT as UNISWAPV2_SWAP_EVENT
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportUniSwapV2SwapEventJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [UniswapV2SwapEvent]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(topics=[UNISWAPV2_SWAP_EVENT.get_signature(), AERODROME_SWAP_EVENT.get_signature()]),
            ]
        )

    def _process(self, **kwargs):
        logs = self._data_buff[Log.type()]
        for log in logs:
            swap_event = None

            if log.topic0 == UNISWAPV2_SWAP_EVENT.get_signature():
                decoded_dict = UNISWAPV2_SWAP_EVENT.decode_log(log)
                swap_event = UniswapV2SwapEvent(
                    pool_address=log.address,
                    sender=decoded_dict["sender"],
                    to_address=decoded_dict["to"],
                    amount0_in=decoded_dict["amount0In"],
                    amount1_in=decoded_dict["amount1In"],
                    amount0_out=decoded_dict["amount0Out"],
                    amount1_out=decoded_dict["amount1Out"],
                    block_number=log.block_number,
                    block_timestamp=log.block_timestamp,
                    transaction_hash=log.transaction_hash,
                    log_index=log.log_index,
                )
            elif log.topic0 == AERODROME_SWAP_EVENT.get_signature():
                decoded_dict = AERODROME_SWAP_EVENT.decode_log(log)
                swap_event = UniswapV2SwapEvent(
                    pool_address=log.address,
                    sender=decoded_dict["sender"],
                    to_address=decoded_dict["to"],
                    amount0_in=decoded_dict["amount0In"],
                    amount1_in=decoded_dict["amount1In"],
                    amount0_out=decoded_dict["amount0Out"],
                    amount1_out=decoded_dict["amount1Out"],
                    block_number=log.block_number,
                    block_timestamp=log.block_timestamp,
                    transaction_hash=log.transaction_hash,
                    log_index=log.log_index,
                )

            if swap_event:
                self._collect_domain(swap_event)
