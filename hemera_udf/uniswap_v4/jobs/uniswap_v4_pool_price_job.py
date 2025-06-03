import json
import logging

import hemera_udf.uniswap_v4.abi.uniswapv4_abi as uniswapv4_abi
from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera_udf.swap.domains.swap_event_domain import UniswapV4SwapEvent
from hemera_udf.token_price.domains import BlockTokenPrice
from hemera_udf.uniswap_v4.domains.feature_uniswap_v4 import (
    UniswapV4Pool,
    UniswapV4PoolCurrentPrice,
    UniswapV4PoolPrice,
)
from hemera_udf.uniswap_v4.models.feature_uniswap_v4_pools import UniswapV4Pools
from hemera_udf.uniswap_v4.util import AddressManager

logger = logging.getLogger(__name__)


class ExportUniSwapV4PoolPriceJob(FilterTransactionDataJob):
    dependency_types = [Transaction, BlockTokenPrice, UniswapV4Pool]
    output_types = [UniswapV4PoolPrice, UniswapV4PoolCurrentPrice, UniswapV4SwapEvent]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config = kwargs["config"]["uniswap_v4_job"]
        jobs = config.get("jobs", [])
        self._pool_address = config.get("pool_address")
        self._address_manager = AddressManager(jobs)

        # WETH address and native ETH address
        self.weth_address = config.get("weth_address", "").lower()
        self.eth_address = uniswapv4_abi.ETH_ADDRESS

        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)
        self.pools_requested_by_rpc = set()
        # self.token_decimals_map = {}

        stable_tokens_config = kwargs["config"].get("export_block_token_price_job", {})

        self.stable_tokens = stable_tokens_config
        self._exist_pools = (
            self.get_existing_pools()
        )  # This needs to be populated in real applications, containing token address to decimals mapping
        self.tokens[self.eth_address] = {**self.tokens.get(self.weth_address, {}), "symbol": "ETH"}
        pass

    def get_filter(self):
        address_list = self._pool_address if self._pool_address else []

        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    topics=[uniswapv4_abi.SWAP_EVENT.get_signature()],
                    addresses=address_list,
                ),
            ]
        )

    def change_block_token_prices_to_dict(self):
        symbol_address_dict = {symbol: address for address, symbol in self.stable_tokens.items()}
        token_prices_dict = {}

        block_token_prices = self._data_buff[BlockTokenPrice.type()]
        for token_price in block_token_prices:
            address = symbol_address_dict.get(token_price.token_symbol)
            if address:
                block_number = token_price.block_number
                token_prices_dict[address, block_number] = token_price.token_price

        return token_prices_dict

    def _process(self, **kwargs):
        token_prices_dict = self.change_block_token_prices_to_dict()

        pools = self._data_buff[UniswapV4Pool.type()]
        for pool in pools:
            self._exist_pools[pool.pool_address.lower()] = {
                "factory_address": pool.factory_address,
                "token0_address": pool.token0_address,
                "token1_address": pool.token1_address,
                "position_token_address": pool.position_token_address,
            }

        transactions = self._data_buff["transaction"]
        current_price_dict = {}
        price_dict = {}

        for transaction in transactions:
            logs = transaction.receipt.logs
            for log in logs:
                if log.topic0 != uniswapv4_abi.SWAP_EVENT.get_signature():
                    continue
                decoded_data = uniswapv4_abi.SWAP_EVENT.decode_log(log)
                pool_id = bytes_to_hex_str(decoded_data["id"]).lower()

                # Check if this pool is in our known pools
                if pool_id in self._exist_pools:
                    pool_data = self._exist_pools[pool_id].copy()
                    factory_address = pool_data.pop("factory_address")
                    key_data_dict = {
                        "tick": decoded_data["tick"],
                        "sqrt_price_x96": decoded_data["sqrtPriceX96"],
                        "block_number": log.block_number,
                        "block_timestamp": log.block_timestamp,
                        "pool_address": pool_id,  # Use pool_id as identifier
                    }

                    token0_address = pool_data.get("token0_address")
                    token1_address = pool_data.get("token1_address")

                    tokens0 = self.tokens.get(token0_address)
                    tokens1 = self.tokens.get(token1_address)

                    decimals0 = tokens0.get("decimals") if tokens0 else None
                    decimals1 = tokens1.get("decimals") if tokens1 else None

                    amount0 = decoded_data["amount0"]
                    amount1 = decoded_data["amount1"]

                    amount0_abs = abs(amount0)
                    amount1_abs = abs(amount1)

                    decimals_conditions = decimals0 and decimals1

                    # Price calculation logic, similar to v3
                    if token0_address in self.stable_tokens and decimals_conditions:
                        token0_price = token_prices_dict.get((token0_address, log.block_number))
                        amount_usd = amount0_abs / 10**decimals0 * token0_price if token0_price else None
                        token1_price = (
                            amount_usd / (amount1_abs / 10**decimals1) if amount1_abs > 0 and amount_usd else None
                        )
                    elif token1_address in self.stable_tokens and decimals_conditions:
                        token1_price = token_prices_dict.get((token1_address, log.block_number))
                        amount_usd = amount1_abs / 10**decimals1 * token1_price if token1_price else None
                        token0_price = (
                            amount_usd / (amount0_abs / 10**decimals0) if amount0_abs > 0 and amount_usd else None
                        )
                    else:
                        token0_price = None
                        token1_price = None
                        amount_usd = None

                    # Create price record
                    pool_price_item = UniswapV4PoolPrice(
                        **key_data_dict,
                        factory_address=factory_address,
                        token0_price=token0_price,
                        token1_price=token1_price,
                    )
                    price_dict[pool_id, log.block_number] = pool_price_item
                    current_price_dict[pool_id] = UniswapV4PoolCurrentPrice(**vars(pool_price_item))

                    # Create swap event record
                    self._collect_domain(
                        UniswapV4SwapEvent(
                            project="uniswap",
                            version=4,
                            transaction_hash=log.transaction_hash,
                            transaction_from_address=transaction.from_address,
                            log_index=log.log_index,
                            sender=decoded_data["sender"],
                            recipient=None,  # v4 SWAP event doesn't include recipient
                            amount0=amount0,
                            amount1=amount1,
                            liquidity=decoded_data["liquidity"],
                            **key_data_dict,
                            **pool_data,
                            token0_price=token0_price,
                            token1_price=token1_price,
                            amount_usd=amount_usd,
                            hook_data=None,  # May need to process hookData here
                        ),
                    )

        # Collect all price records
        self._collect_domains(price_dict.values())
        self._collect_domains(list(current_price_dict.values()))

    def get_existing_pools(self):
        session = self._service.Session()
        try:
            pools_orm = session.query(UniswapV4Pools).all()
            existing_pools = {
                bytes_to_hex_str(p.pool_address).lower(): {
                    "token0_address": bytes_to_hex_str(p.token0_address),
                    "token1_address": bytes_to_hex_str(p.token1_address),
                    "position_token_address": bytes_to_hex_str(p.position_token_address),
                    "factory_address": bytes_to_hex_str(p.factory_address),
                }
                for p in pools_orm
            }
        except Exception as e:
            logger.error(f"Failed to get existing pools: {e}")
            existing_pools = {}
        finally:
            session.close()

        return existing_pools
