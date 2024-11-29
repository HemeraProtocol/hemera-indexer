import logging

import indexer.modules.custom.uniswap_v3.agni_abi as agni_abi
import indexer.modules.custom.uniswap_v3.swapsicle_abi as swapsicle_abi
import indexer.modules.custom.uniswap_v3.uniswapv3_abi as uniswapv3_abi
from common.utils.format_utils import bytes_to_hex_str
from indexer.domain.transaction import Transaction
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.uniswap_v3.domains.feature_uniswap_v3 import (
    UniswapV3PoolCurrentPrice,
    UniswapV3PoolFromSwapEvent,
    UniswapV3PoolPrice,
    UniswapV3SwapEvent,
)
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper

logger = logging.getLogger(__name__)


class ExportUniSwapV3PoolJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [UniswapV3PoolPrice, UniswapV3PoolCurrentPrice, UniswapV3SwapEvent, UniswapV3PoolFromSwapEvent]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config = kwargs["config"]["uniswap_v3_job"]

        position_token_address = config.get("position_token_address")
        self.factory_position_pair = {}

        for d_list in position_token_address.values():
            for d in d_list:
                self.factory_position_pair.update(d)

        self._pool_address = config.get("pool_address")
        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)

    def get_filter(self):
        address_list = self._pool_address if self._pool_address else []

        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    topics=[
                        # Uniswapv3/cle
                        uniswapv3_abi.SWAP_EVENT.get_signature(),
                        # agni/fusionx
                        agni_abi.SWAP_EVENT.get_signature(),
                        # swapsicle
                        swapsicle_abi.SWAP_EVENT.get_signature(),
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

        # pool_logs
        missing_pool_address_dict = {}
        #  fee/factory/token0/token1

        for transaction in transactions:
            logs = transaction.receipt.logs
            for log in logs:
                abi_module = None

                if log.topic0 == uniswapv3_abi.SWAP_EVENT.get_signature() and log.address not in self._exist_pools:
                    abi_module = uniswapv3_abi
                elif log.topic0 == swapsicle_abi.SWAP_EVENT.get_signature() and log.address not in self._exist_pools:
                    abi_module = swapsicle_abi
                elif log.topic0 == agni_abi.SWAP_EVENT.get_signature() and log.address not in self._exist_pools:
                    abi_module = agni_abi
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
            factory_address = factory_call.returns.get("")
            if factory_address:
                position_token_address = self.factory_position_pair.get(factory_address)
                if position_token_address:
                    fee = fee_call.returns.get("", 0)
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

        for transaction in transactions:
            logs = transaction.receipt.logs
            for log in logs:
                if log.address in self._exist_pools:
                    pool_address = log.address
                    pool_data = self._exist_pools[pool_address].copy()
                    factory_address = pool_data.pop("factory_address")
                    key_data_dict = {}
                    decoded_data = {}
                    if log.topic0 == uniswapv3_abi.SWAP_EVENT.get_signature():
                        decoded_data = uniswapv3_abi.SWAP_EVENT.decode_log(log)
                        key_data_dict = {
                            "tick": decoded_data["tick"],
                            "sqrt_price_x96": decoded_data["sqrtPriceX96"],
                            "block_number": log.block_number,
                            "block_timestamp": log.block_timestamp,
                            "pool_address": pool_address,
                        }

                    elif log.topic0 == agni_abi.SWAP_EVENT.get_signature():
                        decoded_data = agni_abi.SWAP_EVENT.decode_log(log)
                        key_data_dict = {
                            "tick": decoded_data["tick"],
                            "sqrt_price_x96": decoded_data["sqrtPriceX96"],
                            "block_number": log.block_number,
                            "block_timestamp": log.block_timestamp,
                            "pool_address": pool_address,
                        }

                    elif log.topic0 == swapsicle_abi.SWAP_EVENT.get_signature():
                        decoded_data = swapsicle_abi.SWAP_EVENT.decode_log(log)
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
