import random
from hemera.common.utils.format_utils import hex_str_to_bytes
from hemera.indexer.domains.token_transfer import ERC20TokenTransfer
from hemera.indexer.jobs.base_job import ExtensionJob
from hemera_udf.token_holder_metrics.domains.metrics import TokenHolderMetricsCurrentD, TokenHolderMetricsHistoryD
from hemera_udf.token_holder_metrics.models.metrics import TokenHolderMetricsCurrent
from hemera_udf.token_price.models import AfDexBlockTokenPrice
from hemera_udf.uniswap_v2.domains import UniswapV2SwapEvent
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import UniswapV3SwapEvent


class ExportTokenHolderMetricsJob(ExtensionJob):
    dependency_types = [ERC20TokenTransfer, UniswapV2SwapEvent, UniswapV3SwapEvent]
    output_types = [TokenHolderMetricsCurrentD, TokenHolderMetricsHistoryD]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = kwargs["config"].get("db_service")

    def _collect(self, **kwargs):
        pass

    def _process(self, **kwargs):
        transfers = self._data_buff[ERC20TokenTransfer.type()]
        swaps = self._data_buff[UniswapV2SwapEvent.type()] + self._data_buff[UniswapV3SwapEvent.type()]
        swap_txs = {swap.transaction_hash: swap for swap in swaps}

        history_metrics = []
        for transfer in transfers:
            token_holder_from_metrics = TokenHolderMetricsHistoryD(
                holder_address=transfer.from_address,
                token_address=transfer.token_address,
                block_number=transfer.block_number,
                block_timestamp=transfer.block_timestamp,
                transfer_amount=transfer.value,
                is_swap=False,
                transfer_action="out",
                tx_hash=transfer.transaction_hash,
                tx_index=transfer.log_index,
            )
            token_holder_to_metrics = TokenHolderMetricsHistoryD(
                holder_address=transfer.to_address,
                token_address=transfer.token_address,
                block_number=transfer.block_number,
                block_timestamp=transfer.block_timestamp,
                transfer_amount=transfer.value,
                is_swap=False,
                transfer_action="in",
                tx_hash=transfer.transaction_hash,
                tx_index=transfer.log_index,
            )
            swap = swap_txs.get(transfer.transaction_hash)
            if swap:
                if swap.sender == transfer.from_address:
                    token_holder_from_metrics.is_buy = True
                    token_holder_from_metrics.is_swap = True
                elif (hasattr(swap, 'to_address') and swap.to_address == transfer.from_address) or \
                        (hasattr(swap, 'recipient') and swap.recipient == transfer.from_address):
                    token_holder_from_metrics.is_swap = True
                if swap.sender == transfer.to_address:
                    token_holder_to_metrics.is_buy = True
                    token_holder_to_metrics.is_swap = True
                elif (hasattr(swap, 'to_address') and swap.to_address == transfer.to_address) or \
                        (hasattr(swap, 'recipient') and swap.recipient == transfer.to_address):
                    token_holder_to_metrics.is_swap = True
            price = self._get_token_dex_price_latest(transfer.token_address, transfer.block_number)
            token = self.tokens[transfer.token_address]
            amount_usd = transfer.value * price / 10 ** token['decimals']
            token_holder_from_metrics.price_usd = price
            token_holder_from_metrics.transfer_usd = amount_usd
            token_holder_to_metrics.price_usd = price
            token_holder_to_metrics.transfer_usd = amount_usd
            history_metrics.append(token_holder_from_metrics)
            history_metrics.append(token_holder_to_metrics)

        current_metrics = {}
        for metrics in history_metrics:
            self._collect_domain(metrics)
            if metrics.holder_address not in current_metrics:
                current_metrics[metrics.holder_address] = {}
            if metrics.token_address not in current_metrics[metrics.holder_address]:
                current_metrics[metrics.holder_address][metrics.token_address] = self._get_address_token_holder_metrics(
                    metrics.holder_address, metrics.token_address)
                if not current_metrics[metrics.holder_address][metrics.token_address]:
                    current_metrics[metrics.holder_address][metrics.token_address] = TokenHolderMetricsCurrentD(
                        holder_address=metrics.holder_address,
                        token_address=metrics.token_address,
                        block_number=metrics.block_number,
                        block_timestamp=metrics.block_timestamp,
                        first_block_timestamp=metrics.block_timestamp,
                        last_swap_timestamp=metrics.block_timestamp,
                        last_transfer_timestamp=metrics.block_timestamp,
                    )
            now_metrics = current_metrics[metrics.holder_address][metrics.token_address]

            if metrics.transfer_action == "in":
                new_amount = metrics.transfer_amount
                new_cost = metrics.transfer_usd
                old_amount = now_metrics.current_balance
                old_cost = old_amount * now_metrics.current_average_buy_price if old_amount > 0 else 0

                now_metrics.current_balance += new_amount
                total_cost = old_cost + new_cost

                if now_metrics.current_balance > 0:
                    now_metrics.current_average_buy_price = total_cost / now_metrics.current_balance

                now_metrics.total_buy_count += 1
                now_metrics.total_buy_amount += new_amount
                now_metrics.total_buy_usd += new_cost

            else:
                sell_amount = metrics.transfer_amount
                sell_price = metrics.price_usd

                if now_metrics.current_balance > 0:
                    profit = (sell_price - now_metrics.current_average_buy_price) * sell_amount
                    now_metrics.realized_pnl += profit

                    if sell_price > now_metrics.current_average_buy_price:
                        now_metrics.success_sell_count += 1
                    else:
                        now_metrics.fail_sell_count += 1

                    total_sells = now_metrics.success_sell_count + now_metrics.fail_sell_count
                    if total_sells > 0:
                        now_metrics.win_rate = now_metrics.success_sell_count / total_sells

                now_metrics.current_balance -= sell_amount

                now_metrics.total_sell_count += 1
                now_metrics.total_sell_amount += sell_amount
                now_metrics.total_sell_usd += metrics.transfer_usd

            
            if now_metrics.current_balance >= now_metrics.max_balance:
                now_metrics.max_balance = now_metrics.current_balance
                now_metrics.max_balance_timestamp = metrics.block_timestamp
                now_metrics.sell_25_timestamp = 0
                now_metrics.sell_50_timestamp = 0

            if now_metrics.current_balance <= now_metrics.max_balance * 0.75 and now_metrics.sell_25_timestamp == 0:
                now_metrics.sell_25_timestamp = metrics.block_timestamp
            if now_metrics.current_balance <= now_metrics.max_balance * 0.5 and now_metrics.sell_50_timestamp == 0:
                now_metrics.sell_50_timestamp = metrics.block_timestamp

            if metrics.is_swap:
                now_metrics.last_swap_timestamp = metrics.block_timestamp
                
                if metrics.transfer_action == "in":
                    now_metrics.swap_buy_count += 1
                    now_metrics.swap_buy_amount += metrics.transfer_amount
                    now_metrics.swap_buy_usd += metrics.transfer_usd
                else:
                    now_metrics.swap_sell_count += 1
                    now_metrics.swap_sell_amount += metrics.transfer_amount
                    now_metrics.swap_sell_usd += metrics.transfer_usd

        for holder_metrics in current_metrics.values():
            for token_metrics in holder_metrics.values():
                self._collect_domain(token_metrics)

    def _get_token_dex_price_latest(self, token_address: str, block_number: int):
        token_address_bytes = hex_str_to_bytes(token_address)
        token_price = self._service.get_service_session().query(AfDexBlockTokenPrice).filter(
            AfDexBlockTokenPrice.token_address == token_address_bytes,
            AfDexBlockTokenPrice.block_number <= block_number,
        ).order_by(AfDexBlockTokenPrice.block_number.desc()).first()
        return random.randint(1, 100)
        return token_price.price if token_price else 0.0

    def _get_address_token_holder_metrics(self, address: str, token_address: str):
        token_holder_metrics = self._service.get_service_session().query(TokenHolderMetricsCurrent).filter(
            TokenHolderMetricsCurrent.holder_address == hex_str_to_bytes(address),
            TokenHolderMetricsCurrent.token_address == hex_str_to_bytes(token_address),
        ).first()

        if token_holder_metrics:
            return TokenHolderMetricsCurrentD(
                holder_address=address,
                token_address=token_address,
                block_number=token_holder_metrics.block_number,
                block_timestamp=int(token_holder_metrics.block_timestamp.timestamp()),
                first_block_timestamp=int(token_holder_metrics.first_block_timestamp.timestamp()),
                last_swap_timestamp=int(token_holder_metrics.last_swap_timestamp.timestamp()) if token_holder_metrics.last_swap_timestamp else 0,
                last_transfer_timestamp=int(token_holder_metrics.last_transfer_timestamp.timestamp()) if token_holder_metrics.last_transfer_timestamp else 0,
                current_balance=float(token_holder_metrics.current_balance),
                max_balance=float(token_holder_metrics.max_balance),
                total_buy_count=token_holder_metrics.total_buy_count,
                total_buy_amount=float(token_holder_metrics.total_buy_amount),
                total_buy_usd=float(token_holder_metrics.total_buy_usd),
                total_sell_count=token_holder_metrics.total_sell_count,
                total_sell_amount=float(token_holder_metrics.total_sell_amount),
                total_sell_usd=float(token_holder_metrics.total_sell_usd),
                swap_buy_count=token_holder_metrics.swap_buy_count,
                swap_buy_amount=float(token_holder_metrics.swap_buy_amount),
                swap_buy_usd=float(token_holder_metrics.swap_buy_usd),
                swap_sell_count=token_holder_metrics.swap_sell_count,
                swap_sell_amount=float(token_holder_metrics.swap_sell_amount),
                swap_sell_usd=float(token_holder_metrics.swap_sell_usd),
                success_sell_count=token_holder_metrics.success_sell_count,
                fail_sell_count=token_holder_metrics.fail_sell_count,
                current_average_buy_price=float(token_holder_metrics.current_average_buy_price),
                realized_pnl=float(token_holder_metrics.realized_pnl),
                win_rate=float(token_holder_metrics.win_rate)
            )
        return None
