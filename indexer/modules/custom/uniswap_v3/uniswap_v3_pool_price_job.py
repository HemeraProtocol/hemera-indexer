import logging

from common.utils.format_utils import bytes_to_hex_str
from indexer.domain.transaction import Transaction
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.uniswap_v3.agni_abi import SWAP_EVENT as AGNI_SWAP_EVENT
from indexer.modules.custom.uniswap_v3.domains.feature_uniswap_v3 import (
    UniswapV3PoolCurrentPrice,
    UniswapV3PoolPrice,
    UniswapV3SwapEvent,
)
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from indexer.modules.custom.uniswap_v3.swapsicle_abi import SWAP_EVENT as SICLE_SWAP_EVENT
from indexer.modules.custom.uniswap_v3.uniswapv3_abi import SWAP_EVENT
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)


class ExportUniSwapV3PoolJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [UniswapV3PoolPrice, UniswapV3PoolCurrentPrice, UniswapV3SwapEvent]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config = kwargs["config"]["uniswap_v3_job"]
        self._pool_address = config.get("pool_address")

    def get_filter(self):
        address_list = self._pool_address if self._pool_address else []

        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    topics=[
                        # Uniswapv3/cle
                        SWAP_EVENT.get_signature(),
                        # agni/fusionx
                        AGNI_SWAP_EVENT.get_signature(),
                        # swapsicle
                        SICLE_SWAP_EVENT.get_signature(),
                    ],
                    addresses=address_list,
                ),
            ]
        )

    def _process(self, **kwargs):
        self._exist_pools = self.get_existing_pools()

        transactions = self._data_buff["transaction"]
        current_price_dict = {}
        price_dict = {}

        for transaction in transactions:
            logs = transaction.receipt.logs
            for log in logs:
                if log.address in self._exist_pools:
                    pool_address = log.address
                    pool_data = self._exist_pools[pool_address].copy()
                    factory_address = pool_data.pop("factory_address")
                    key_data_dict = {}
                    decoded_data = {}
                    if log.topic0 == SWAP_EVENT.get_signature():
                        decoded_data = SWAP_EVENT.decode_log(log)
                        key_data_dict = {
                            "tick": decoded_data["tick"],
                            "sqrt_price_x96": decoded_data["sqrtPriceX96"],
                            "block_number": log.block_number,
                            "block_timestamp": log.block_timestamp,
                            "pool_address": pool_address,
                        }

                    elif log.topic0 == AGNI_SWAP_EVENT.get_signature():
                        decoded_data = AGNI_SWAP_EVENT.decode_log(log)
                        key_data_dict = {
                            "tick": decoded_data["tick"],
                            "sqrt_price_x96": decoded_data["sqrtPriceX96"],
                            "block_number": log.block_number,
                            "block_timestamp": log.block_timestamp,
                            "pool_address": pool_address,
                        }

                    elif log.topic0 == SICLE_SWAP_EVENT.get_signature():
                        decoded_data = SICLE_SWAP_EVENT.decode_log(log)
                        key_data_dict = {
                            "tick": decoded_data["tick"],
                            "sqrt_price_x96": decoded_data["price"],
                            "block_number": log.block_number,
                            "block_timestamp": log.block_timestamp,
                            "pool_address": pool_address,
                        }

                    if decoded_data:
                        price = UniswapV3PoolPrice(**key_data_dict, factory_address=factory_address)
                        price_dict[pool_address, log.block_number] = price
                        current_price_dict[pool_address] = UniswapV3PoolCurrentPrice(**vars(price))

                        self._collect_domain(
                            UniswapV3SwapEvent(
                                transaction_hash=log.transaction_hash,
                                transaction_from_address=transaction.from_address,
                                log_index=log.log_index,
                                sender=decoded_data["sender"],
                                recipient=decoded_data["recipient"],
                                amount0=decoded_data["amount0"],
                                amount1=decoded_data["amount1"],
                                liquidity=decoded_data["liquidity"],
                                **key_data_dict,
                                **pool_data,
                            ),
                        )

        self._collect_domains(price_dict.values())
        self._collect_domains(list(current_price_dict.values()))

    def get_existing_pools(self):
        session = self._service.Session()
        try:
            pools_orm = session.query(UniswapV3Pools).all()
            existing_pools = {
                bytes_to_hex_str(p.pool_address): {
                    "token0_address": bytes_to_hex_str(p.token0_address),
                    "token1_address": bytes_to_hex_str(p.token1_address),
                    "position_token_address": bytes_to_hex_str(p.position_token_address),
                    "factory_address": bytes_to_hex_str(p.factory_address),
                }
                for p in pools_orm
            }

        except Exception as e:
            print(e)
            raise e
        finally:
            session.close()

        return existing_pools
