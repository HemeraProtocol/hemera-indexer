import logging

from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.indexer.domains.log import Log
from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera_udf.swap.domains.swap_event_domain import UniswapV2SwapEvent
from hemera_udf.token_price.domains import BlockTokenPrice
from hemera_udf.uniswap_v2.abi import aerodromev2_abi, uniswapv2_abi
from hemera_udf.uniswap_v2.abi.aerodromev2_abi import SWAP_EVENT as AERODROME_SWAP_EVENT
from hemera_udf.uniswap_v2.abi.uniswapv2_abi import SWAP_EVENT as UNISWAPV2_SWAP_EVENT
from hemera_udf.uniswap_v2.domains import UniswapV2PoolFromSwapEvent
from hemera_udf.uniswap_v2.models.feature_uniswap_v2_pools import UniswapV2Pools

logger = logging.getLogger(__name__)


class ExportUniSwapV2SwapEventJob(FilterTransactionDataJob):
    dependency_types = [Transaction, BlockTokenPrice]
    output_types = [UniswapV2SwapEvent, UniswapV2PoolFromSwapEvent]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        stable_tokens_config = kwargs["config"].get("export_block_token_price_job", {})

        self.stable_tokens = stable_tokens_config
        self.pools_requested_by_rpc = set()
        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)
        self._existing_pools = self.get_existing_pools()

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(topics=[UNISWAPV2_SWAP_EVENT.get_signature(), AERODROME_SWAP_EVENT.get_signature()]),
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

        transactions = self._data_buff["transaction"]

        for transaction in transactions:
            logs = transaction.receipt.logs
            for log in logs:
                abi_module = None
                if log.topic0 == UNISWAPV2_SWAP_EVENT.get_signature() and log.address not in self._existing_pools:
                    if log.address not in self.pools_requested_by_rpc:
                        abi_module = uniswapv2_abi
                        self.pools_requested_by_rpc.add(log.address)
                elif log.topic0 == AERODROME_SWAP_EVENT.get_signature() and log.address not in self._existing_pools:
                    if log.address not in self.pools_requested_by_rpc:
                        abi_module = aerodromev2_abi
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
        token0_list = []
        token1_list = []

        for call_dict in missing_pool_address_dict.values():
            abi_module = call_dict.pop("abi_module")
            factory_list.append(Call(function_abi=abi_module.FACTORY_FUNCTION, **call_dict))
            token0_list.append(Call(function_abi=abi_module.TOKEN0_FUNCTION, **call_dict))
            token1_list.append(Call(function_abi=abi_module.TOKEN1_FUNCTION, **call_dict))

        self.multi_call_helper.execute_calls(factory_list)
        self.multi_call_helper.execute_calls(token0_list)
        self.multi_call_helper.execute_calls(token1_list)

        for factory_call, token0_call, token1_call in zip(factory_list, token0_list, token1_list):
            factory_address = factory_call.returns.get("") if factory_call.returns else None
            token0 = token0_call.returns.get("") if token0_call.returns else None
            token1 = token1_call.returns.get("") if token1_call.returns else None
            if factory_address and token0 and token1:
                pool_address = factory_call.target.lower()
                uniswap_v_pool_from_swap_event = UniswapV2PoolFromSwapEvent(
                    factory_address=factory_address,
                    pool_address=pool_address,
                    token0_address=token0,
                    token1_address=token1,
                    block_number=factory_call.block_number,
                    block_timestamp=factory_call.user_defined_k,
                    length=-1,
                )

                self._existing_pools[pool_address] = token0, token1
                self._collect_domain(uniswap_v_pool_from_swap_event)

    def _process(self, **kwargs):
        self.get_missing_pools_by_rpc()

        token_prices_dict = self.change_block_token_prices_to_dict()

        transactions = self._data_buff[Transaction.type()]
        for transaction in transactions:
            logs = transaction.receipt.logs
            for log in logs:
                decoded_dict = None
                block_number = log.block_number
                if log.topic0 == UNISWAPV2_SWAP_EVENT.get_signature() and log.address in self._existing_pools:
                    decoded_dict = UNISWAPV2_SWAP_EVENT.decode_log(log)
                elif log.topic0 == AERODROME_SWAP_EVENT.get_signature() and log.address in self._existing_pools:
                    decoded_dict = AERODROME_SWAP_EVENT.decode_log(log)

                if decoded_dict:
                    amount0_in = decoded_dict["amount0In"]
                    amount1_in = decoded_dict["amount1In"]
                    amount0_out = decoded_dict["amount0Out"]
                    amount1_out = decoded_dict["amount1Out"]

                    amount0 = amount0_in - amount0_out
                    amount1 = amount1_in - amount1_out

                    amount0_abs = abs(amount0)
                    amount1_abs = abs(amount1)

                    token0_address, token1_address = self._existing_pools[log.address]

                    tokens0 = self.tokens.get(token0_address)
                    tokens1 = self.tokens.get(token1_address)

                    decimals0 = tokens0.get("decimals") if tokens0 else None
                    decimals1 = tokens1.get("decimals") if tokens1 else None

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

                    swap_event = UniswapV2SwapEvent(
                        project="uniswap",
                        version=2,
                        pool_address=log.address,
                        sender=decoded_dict["sender"],
                        to_address=decoded_dict["to"],
                        amount0_in=amount0_in,
                        amount1_in=amount1_in,
                        amount0_out=amount0_out,
                        amount1_out=amount1_out,
                        block_number=block_number,
                        block_timestamp=log.block_timestamp,
                        transaction_hash=log.transaction_hash,
                        transaction_from_address=transaction.from_address,
                        log_index=log.log_index,
                        token0_price=token0_price,
                        token1_price=token1_price,
                        amount_usd=amount_usd,
                        amount0=amount0,
                        amount1=amount1,
                        token0_address=token0_address,
                        token1_address=token1_address,
                    )

                    self._collect_domain(swap_event)
        pass

    def get_existing_pools(self):
        session = self._service.Session()
        try:
            existing_pools = {}

            pools_orm = session.query(UniswapV2Pools).all()
            for pool in pools_orm:
                existing_pools[bytes_to_hex_str(pool.pool_address)] = bytes_to_hex_str(
                    pool.token0_address
                ), bytes_to_hex_str(pool.token1_address)

        except Exception as e:
            print(e)
            raise e
        finally:
            session.close()

        return existing_pools
