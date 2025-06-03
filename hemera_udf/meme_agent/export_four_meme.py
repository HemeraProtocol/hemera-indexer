import logging
from typing import List

from hemera.indexer.domains.log import Log
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera_udf.meme_agent.abi.fourmeme_event import (
    GET_TOKEN_INFO_FUNCTION,
    token_create_event,
    token_purchase_event,
    token_sale_event,
)
from hemera_udf.meme_agent.domains.fourmeme import FourMemeTokenCreateD, FourMemeTokenTradeD
from hemera_udf.swap.domains.swap_event_domain import FourMemeSwapEvent
from hemera_udf.token_price.domains import BlockTokenPrice

logger = logging.getLogger(__name__)


class ExportFourMemeJob(FilterTransactionDataJob):
    """Job for exporting FourMeme protocol events"""

    dependency_types = [Log, BlockTokenPrice]
    output_types = [FourMemeSwapEvent]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)
        self.quote_token_dict = {}
        # maybe can be replaced by config
        self.contract = "0xf251f83e40a78868fcfa3fa4599dad6494e46034"
        self.bnb_address = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
        self.zero_address = "0x0000000000000000000000000000000000000000"
        stable_tokens_config = kwargs["config"].get("export_block_token_price_job", {})

        self.stable_tokens = stable_tokens_config

        self.events = {
            token_create_event.get_signature(): token_create_event,
            token_purchase_event.get_signature(): token_purchase_event,
            token_sale_event.get_signature(): token_sale_event,
        }

    def get_filter(self):
        if self._chain_id == 56:
            """Get event filter specification"""
            addresses = [self.user_defined_config.get("token_manager2_addresses")]
            topics = [
                token_create_event.get_signature(),
                token_purchase_event.get_signature(),
                token_sale_event.get_signature(),
            ]
        else:
            addresses = []
            topics = []

        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    addresses=addresses,
                    topics=topics,
                )
            ]
        )

    def get_wbnb_prices_dict(self):
        wbnb_prices_dict = {}

        block_token_prices = self._data_buff[BlockTokenPrice.type()]
        for token_price in block_token_prices:
            if token_price.token_symbol == "WBNB":
                block_number = token_price.block_number
                wbnb_prices_dict[block_number] = token_price.token_price

        self.wbnb_prices_dict = wbnb_prices_dict

    def _collect(self, **kwargs):
        pass

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
        if self._chain_id != 56:
            return

        missing_quote_token_dict = {}

        """Process log events"""
        self.get_wbnb_prices_dict()

        logs: List[Log] = self._data_buff.get(Log.type(), [])
        swap_events = []
        for log in logs:
            if log.topic0 == token_create_event.get_signature():
                # self._process_token_create(log)
                pass

            elif log.topic0 == token_purchase_event.get_signature() or token_sale_event.get_signature():
                if log.topic0 == token_purchase_event.get_signature():
                    trade_type = "buy"
                    log_data = token_purchase_event.decode_log(log)

                else:
                    trade_type = "sell"
                    log_data = token_sale_event.decode_log(log)

                if not log_data:
                    continue

                se = FourMemeSwapEvent(
                    project="fourmeme",
                    version=1,
                    block_number=log.block_number,
                    block_timestamp=log.block_timestamp,
                    transaction_hash=log.transaction_hash,
                    log_index=log.log_index,
                    pool_address=log.address,
                    transaction_from_address=log_data["account"],
                    sender=None,
                    token0_address=log_data["token"],
                    token1_address=self.quote_token_dict.get(log_data["token"]),
                    amount0=None,
                    amount1=None,
                    token0_price=None,
                    token1_price=None,
                    amount_usd=None,
                    price=log_data["price"],
                    amount=log_data["amount"],
                    cost=log_data["cost"],
                    fee=log_data["fee"],
                    offers=log_data["offers"],
                    funds=log_data["funds"],
                    # Type of trade: 'buy' or 'sell'
                    trade_type=trade_type,
                )
                swap_events.append(se)

        for swap_event in swap_events:
            if not swap_event.token1_address:
                call_dict = {
                    "target": self.contract,
                    "block_number": swap_event.block_number,
                    "user_defined_k": swap_event.block_timestamp,
                    "parameters": [swap_event.token0_address],
                }
                call = Call(function_abi=GET_TOKEN_INFO_FUNCTION, **call_dict)
                missing_quote_token_dict[swap_event.token0_address] = call

        self.multi_call_helper.execute_calls(missing_quote_token_dict.values())

        for call_data in missing_quote_token_dict.values():
            if not call_data.returns:
                continue

            quote_token = call_data.returns.get("quote")
            if quote_token == self.zero_address:
                quote_token = self.bnb_address

            self.quote_token_dict[call_data.parameters[0]] = quote_token

        token_prices_dict = self.change_block_token_prices_to_dict()

        for swap_event in swap_events:
            if not swap_event.token1_address:
                swap_event.token1_address = self.quote_token_dict.get(swap_event.token0_address)

            decimals0 = self.tokens.get(swap_event.token0_address, {}).get("decimals")
            decimals1 = self.tokens.get(swap_event.token1_address, {}).get("decimals")

            amount0 = swap_event.amount
            amount1 = swap_event.cost

            amount0_abs = abs(amount0)
            amount1_abs = abs(amount1)

            decimals_conditions = decimals0 and decimals1

            if swap_event.token1_address in self.stable_tokens and decimals_conditions:
                token1_price = token_prices_dict.get((swap_event.token1_address, swap_event.block_number))
                amount_usd = amount1_abs / 10**decimals1 * token1_price
                token0_price = amount_usd / (amount0_abs / 10**decimals0) if amount0_abs > 0 else None
            else:
                token0_price = None
                token1_price = None
                amount_usd = None

            swap_event.token0_price = token0_price
            swap_event.token1_price = token1_price
            swap_event.amount_usd = amount_usd

            if swap_event.trade_type == "buy":
                # buy, meme token is decreased for pool, stable token is increased for pool
                swap_event.amount0 = -amount0 if amount0 is not None else None
                swap_event.amount1 = amount1 if amount1 is not None else None
            else:
                # sell, meme token is increased for pool, stable token is decreased for pool
                swap_event.amount0 = amount0 if amount0 is not None else None
                swap_event.amount1 = -amount1 if amount1 is not None else None
            self._collect_domain(swap_event)

            pass

    def _process_token_create(self, log: Log):
        """Process token creation event"""
        log_data = token_create_event.decode_log(log)
        if not log_data:
            return

        self._collect_domain(
            FourMemeTokenCreateD(
                creator=log_data["creator"],
                token=log_data["token"],
                request_id=log_data["requestId"],
                name=log_data["name"],
                symbol=log_data["symbol"],
                total_supply=log_data["totalSupply"],
                launch_time=log_data["launchTime"],
                launch_fee=log_data["launchFee"],
                block_number=log.block_number,
                block_timestamp=log.block_timestamp,
                transaction_hash=log.transaction_hash,
            )
        )

    def _process_token_purchase(self, log: Log):
        """Process token purchase event"""
        log_data = token_purchase_event.decode_log(log)
        if not log_data:
            return

        wbnb_usd_price = self.wbnb_prices_dict.get(log.block_number, 0)

        price_usd = float(log_data["price"]) * float(wbnb_usd_price) / 10.0**18

        self._collect_domain(
            FourMemeTokenTradeD(
                token=log_data["token"],
                account=log_data["account"],
                log_index=log.log_index,
                price=log_data["price"],
                price_usd=price_usd,
                amount=log_data["amount"],
                cost=log_data["cost"],
                fee=log_data["fee"],
                offers=log_data["offers"],
                funds=log_data["funds"],
                block_number=log.block_number,
                block_timestamp=log.block_timestamp,
                trade_type="buy",
                transaction_hash=log.transaction_hash,
            )
        )

    def _process_token_sale(self, log: Log):
        """Process token sale event"""
        log_data = token_sale_event.decode_log(log)
        if not log_data:
            return

        wbnb_usd_price = self.wbnb_prices_dict.get(log.block_number, 0)

        price_usd = float(log_data["price"]) * float(wbnb_usd_price) / 10.0**18

        self._collect_domain(
            FourMemeTokenTradeD(
                token=log_data["token"],
                account=log_data["account"],
                log_index=log.log_index,
                price=log_data["price"],
                price_usd=price_usd,
                amount=log_data["amount"],
                cost=log_data["cost"],
                fee=log_data["fee"],
                offers=log_data["offers"],
                funds=log_data["funds"],
                block_number=log.block_number,
                block_timestamp=log.block_timestamp,
                trade_type="sell",
                transaction_hash=log.transaction_hash,
            )
        )
