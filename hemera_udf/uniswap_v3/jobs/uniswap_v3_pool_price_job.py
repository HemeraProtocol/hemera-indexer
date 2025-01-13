import logging

import hemera_udf.uniswap_v3.abi.agni_abi as agni_abi
import hemera_udf.uniswap_v3.abi.swapsicle_abi as swapsicle_abi
import hemera_udf.uniswap_v3.abi.uniswapv3_abi as uniswapv3_abi
from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera_udf.token_price.domains import BlockTokenPrice
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import (
    UniswapV3PoolCurrentPrice,
    UniswapV3PoolFromSwapEvent,
    UniswapV3PoolPrice,
    UniswapV3SwapEvent,
)
from hemera_udf.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from hemera_udf.uniswap_v3.util import AddressManager

logger = logging.getLogger(__name__)


class ExportUniSwapV3PoolPriceJob(FilterTransactionDataJob):
    dependency_types = [Transaction, BlockTokenPrice]
    output_types = [UniswapV3PoolPrice, UniswapV3PoolCurrentPrice, UniswapV3SwapEvent, UniswapV3PoolFromSwapEvent]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config = kwargs["config"]["uniswap_v3_job"]
        jobs = config.get("jobs", [])
        self._pool_address = config.get("pool_address")
        self._address_manager = AddressManager(jobs)

        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)
        self.pools_requested_by_rpc = set()
        # self.token_decimals_map = {}

        stable_tokens_config = kwargs["config"].get("export_block_token_price_job", {})

        self.stable_tokens = stable_tokens_config

    def get_filter(self):
        address_list = self._pool_address if self._pool_address else []

        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    topics=[
                        abi_module.SWAP_EVENT.get_signature() for abi_module in self._address_manager.abi_modules_list
                    ],
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

    def get_missing_pools_by_rpc(self):
        # pool_logs
        missing_pool_address_dict = {}
        #  fee/factory/token0/token1
        transactions = self._data_buff["transaction"]

        for transaction in transactions:
            logs = transaction.receipt.logs
            for log in logs:
                abi_module = None
                if log.topic0 == uniswapv3_abi.SWAP_EVENT.get_signature() and log.address not in self._exist_pools:
                    if log.address not in self.pools_requested_by_rpc:
                        abi_module = uniswapv3_abi
                        self.pools_requested_by_rpc.add(log.address)
                elif log.topic0 == swapsicle_abi.SWAP_EVENT.get_signature() and log.address not in self._exist_pools:
                    if log.address not in self.pools_requested_by_rpc:
                        abi_module = swapsicle_abi
                        self.pools_requested_by_rpc.add(log.address)
                elif log.topic0 == agni_abi.SWAP_EVENT.get_signature() and log.address not in self._exist_pools:
                    if log.address not in self.pools_requested_by_rpc:
                        abi_module = agni_abi
                        self.pools_requested_by_rpc.add(log.address)

                if abi_module:
                    call_dict = {
                        "abi_module": abi_module,
                        "target": log.address,
                        "block_number": log.block_number,
                        "user_defined_k": log.block_timestamp,
                    }
                    missing_pool_address_dict[log.address] = call_dict

        factory_list = []
        fee_list = []
        token0_list = []
        token1_list = []
        tick_spacing_list = []

        for call_dict in missing_pool_address_dict.values():
            abi_module = call_dict.pop("abi_module")
            factory_list.append(Call(function_abi=abi_module.FACTORY_FUNCTION, **call_dict))
            fee_list.append(Call(function_abi=abi_module.FEE_FUNCTION, **call_dict))
            token0_list.append(Call(function_abi=abi_module.TOKEN0_FUNCTION, **call_dict))
            token1_list.append(Call(function_abi=abi_module.TOKEN1_FUNCTION, **call_dict))
            tick_spacing_list.append(Call(function_abi=abi_module.TICK_SPACING_FUNCTION, **call_dict))

        self.multi_call_helper.execute_calls(factory_list)
        self.multi_call_helper.execute_calls(fee_list)
        self.multi_call_helper.execute_calls(token0_list)
        self.multi_call_helper.execute_calls(token1_list)
        self.multi_call_helper.execute_calls(tick_spacing_list)

        for factory_call, fee_call, token0_call, token1_call, tick_spacing_call in zip(
            factory_list, fee_list, token0_list, token1_list, tick_spacing_list
        ):
            factory_address = factory_call.returns.get("") if factory_call.returns else None
            if factory_address:
                position_token_address = self._address_manager.get_position_by_factory(factory_address)
                if position_token_address:
                    if fee_call.returns:
                        fee = fee_call.returns.get("", 0)
                    else:
                        fee = 0
                    token0 = token0_call.returns.get("")
                    token1 = token1_call.returns.get("")
                    pool_address = factory_call.target.lower()
                    tick_spacing = tick_spacing_call.returns.get("", 0)

                    uniswap_v_pool_from_swap_event = UniswapV3PoolFromSwapEvent(
                        position_token_address=position_token_address,
                        factory_address=factory_address,
                        pool_address=pool_address,
                        fee=fee,
                        token0_address=token0,
                        token1_address=token1,
                        block_number=factory_call.block_number,
                        block_timestamp=factory_call.user_defined_k,
                        tick_spacing=tick_spacing,
                    )

                    self._exist_pools[pool_address] = {
                        "token0_address": token0,
                        "token1_address": token1,
                        "position_token_address": position_token_address,
                        "factory_address": factory_address,
                    }
                    self._collect_domain(uniswap_v_pool_from_swap_event)

    def _process(self, **kwargs):
        self._exist_pools = self.get_existing_pools()
        token_prices_dict = self.change_block_token_prices_to_dict()

        if not self._pool_address:
            self.get_missing_pools_by_rpc()

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
                    block_number = log.block_number
                    if log.topic0 == uniswapv3_abi.SWAP_EVENT.get_signature():
                        decoded_data = uniswapv3_abi.SWAP_EVENT.decode_log(log)
                        key_data_dict = {
                            "tick": decoded_data["tick"],
                            "sqrt_price_x96": decoded_data["sqrtPriceX96"],
                            "block_number": block_number,
                            "block_timestamp": log.block_timestamp,
                            "pool_address": pool_address,
                        }

                    elif log.topic0 == agni_abi.SWAP_EVENT.get_signature():
                        decoded_data = agni_abi.SWAP_EVENT.decode_log(log)
                        key_data_dict = {
                            "tick": decoded_data["tick"],
                            "sqrt_price_x96": decoded_data["sqrtPriceX96"],
                            "block_number": block_number,
                            "block_timestamp": log.block_timestamp,
                            "pool_address": pool_address,
                        }

                    elif log.topic0 == swapsicle_abi.SWAP_EVENT.get_signature():
                        # maybe can be removed
                        decoded_data = swapsicle_abi.SWAP_EVENT.decode_log(log)
                        key_data_dict = {
                            "tick": decoded_data["tick"],
                            "sqrt_price_x96": decoded_data["price"],
                            "block_number": block_number,
                            "block_timestamp": log.block_timestamp,
                            "pool_address": pool_address,
                        }

                    if decoded_data:
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

                        if token0_address in self.stable_tokens and decimals_conditions:
                            token0_price = token_prices_dict.get((token0_address, block_number))
                            amount_usd = amount0_abs / 10**decimals0 * token0_price
                            token1_price = amount_usd / (amount1_abs / 10**decimals1) if amount1_abs > 0 else None

                        elif token1_address in self.stable_tokens and decimals_conditions:
                            token1_price = token_prices_dict.get((token1_address, block_number))
                            amount_usd = amount1_abs / 10**decimals1 * token1_price
                            token0_price = amount_usd / (amount0_abs / 10**decimals0) if amount0_abs > 0 else None
                        else:
                            token0_price = None
                            token1_price = None
                            amount_usd = None

                        pool_price_item = UniswapV3PoolPrice(
                            **key_data_dict,
                            factory_address=factory_address,
                            token0_price=token0_price,
                            token1_price=token1_price,
                        )
                        price_dict[pool_address, block_number] = pool_price_item
                        current_price_dict[pool_address] = UniswapV3PoolCurrentPrice(**vars(pool_price_item))

                        self._collect_domain(
                            UniswapV3SwapEvent(
                                transaction_hash=log.transaction_hash,
                                transaction_from_address=transaction.from_address,
                                log_index=log.log_index,
                                sender=decoded_data["sender"],
                                recipient=decoded_data["recipient"],
                                amount0=amount0,
                                amount1=amount1,
                                liquidity=decoded_data["liquidity"],
                                **key_data_dict,
                                **pool_data,
                                token0_price=token0_price,
                                token1_price=token1_price,
                                amount_usd=amount_usd,
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
