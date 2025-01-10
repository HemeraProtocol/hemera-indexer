from dataclasses import asdict
from hemera.common.utils.format_utils import hex_str_to_bytes, bytes_to_hex_str
from hemera.indexer.domains.token_transfer import ERC20TokenTransfer
from hemera.indexer.jobs.base_job import ExtensionJob
from hemera_udf.token_holder_metrics.domains.metrics import TokenHolderMetricsCurrentD, TokenHolderMetricsHistoryD, \
    TokenHolderTransferWithPriceD
from hemera_udf.token_holder_metrics.models.metrics import TokenHolderMetricsCurrent
from hemera_udf.token_price.models import AfDexBlockTokenPrice
from hemera_udf.uniswap_v2.domains import UniswapV2SwapEvent
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import UniswapV3SwapEvent
from sqlalchemy import or_, text


class ExportTokenHolderMetricsJob(ExtensionJob):
    dependency_types = [ERC20TokenTransfer, UniswapV2SwapEvent, UniswapV3SwapEvent]
    output_types = [TokenHolderMetricsCurrentD, TokenHolderTransferWithPriceD, TokenHolderMetricsHistoryD]
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

        # Collect token-block pairs for batch price query
        token_blocks = [(transfer.token_address, transfer.block_number) for transfer in transfers]
        token_prices = self._get_token_dex_prices_batch(token_blocks)

        transfer_metrics = []
        for transfer in transfers:
            token_holder_from_metrics = TokenHolderTransferWithPriceD(
                holder_address=transfer.from_address,
                token_address=transfer.token_address,
                block_number=transfer.block_number,
                block_timestamp=transfer.block_timestamp,
                transfer_amount=transfer.value,
                is_swap=False,
                transfer_action="out",
                tx_hash=transfer.transaction_hash,
                log_index=transfer.log_index,
            )
            token_holder_to_metrics = TokenHolderTransferWithPriceD(
                holder_address=transfer.to_address,
                token_address=transfer.token_address,
                block_number=transfer.block_number,
                block_timestamp=transfer.block_timestamp,
                transfer_amount=transfer.value,
                is_swap=False,
                transfer_action="in",
                tx_hash=transfer.transaction_hash,
                log_index=transfer.log_index,
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
            price = token_prices.get((transfer.token_address, transfer.block_number), 0.0)
            token = self.tokens[transfer.token_address]
            amount_usd = transfer.value * price / 10 ** token['decimals']
            token_holder_from_metrics.price_usd = price
            token_holder_from_metrics.transfer_usd = amount_usd
            token_holder_to_metrics.price_usd = price
            token_holder_to_metrics.transfer_usd = amount_usd
            transfer_metrics.append(token_holder_from_metrics)
            transfer_metrics.append(token_holder_to_metrics)

        current_metrics = {}
        address_token_pairs = set()
        for metrics in transfer_metrics:
            address_token_pairs.add((metrics.holder_address, metrics.token_address))

        query_results = self._get_address_token_holder_metrics_batch(list(address_token_pairs))
        current_metrics = query_results

        for metrics in transfer_metrics:
            token = self.tokens[metrics.token_address]
            self._collect_domain(metrics)

            key = (metrics.holder_address, metrics.token_address)

            if not current_metrics.get(key):
                current_metrics[key] = TokenHolderMetricsCurrentD(
                    holder_address=metrics.holder_address,
                    token_address=metrics.token_address,
                    block_number=metrics.block_number,
                    block_timestamp=metrics.block_timestamp,
                    first_block_timestamp=metrics.block_timestamp,
                    last_swap_timestamp=metrics.block_timestamp,
                    last_transfer_timestamp=metrics.block_timestamp,
                )
            now_metrics = current_metrics[key]

            if now_metrics.block_number > metrics.block_number:
                continue
            now_metrics.block_number = metrics.block_number
            now_metrics.block_timestamp = metrics.block_timestamp

            if metrics.transfer_action == "in":
                new_amount = metrics.transfer_amount
                new_cost = metrics.transfer_usd
                old_amount = now_metrics.current_balance
                old_cost = old_amount * now_metrics.current_average_buy_price if old_amount > 0 else 0

                now_metrics.current_balance += new_amount
                total_cost = old_cost + new_cost

                now_metrics.total_buy_count += 1
                now_metrics.total_buy_amount += new_amount
                now_metrics.total_buy_usd += new_cost
                if now_metrics.total_buy_amount > 0:
                    now_metrics.current_average_buy_price = now_metrics.total_buy_usd * 10 ** token[
                        'decimals'] / now_metrics.total_buy_amount

            else:
                sell_amount = metrics.transfer_amount
                sell_price = metrics.price_usd

                if now_metrics.current_balance > 0:
                    now_metrics.realized_pnl = now_metrics.total_sell_usd - now_metrics.total_buy_usd + now_metrics.current_balance * metrics.price_usd / 10 ** \
                                               token['decimals']

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

        self._collect_domains(list(current_metrics.values()))
        history_metrics = [TokenHolderMetricsHistoryD(**asdict(metrics)) for metrics in current_metrics.values()]
        self._collect_domains(history_metrics)

    def _get_token_dex_price_latest(self, token_address: str, block_number: int):
        token_address_bytes = hex_str_to_bytes(token_address)
        token_price = self._service.get_service_session().query(AfDexBlockTokenPrice).filter(
            AfDexBlockTokenPrice.token_address == token_address_bytes,
            AfDexBlockTokenPrice.block_number <= block_number,
        ).order_by(AfDexBlockTokenPrice.block_number.desc()).first()
        return token_price.price if token_price else 0.0

    def _get_address_token_holder_metrics_batch(self, address_token_pairs: list[tuple[str, str]]) -> dict[
        tuple[str, str], TokenHolderMetricsCurrentD]:
        if not address_token_pairs:
            return {}

        BATCH_SIZE = 1000
        result = {}
        session = self._service.get_service_session()

        for i in range(0, len(address_token_pairs), BATCH_SIZE):
            batch_pairs = address_token_pairs[i:i + BATCH_SIZE]
            address_bytes_pairs = [(hex_str_to_bytes(addr), hex_str_to_bytes(token))
                                   for addr, token in batch_pairs]

            conditions = [
                (TokenHolderMetricsCurrent.holder_address == holder_addr) &
                (TokenHolderMetricsCurrent.token_address == token_addr)
                for holder_addr, token_addr in address_bytes_pairs
            ]

            batch_results = session.query(TokenHolderMetricsCurrent).filter(
                or_(*conditions)
            ).all()

            for metrics in batch_results:
                key = (bytes_to_hex_str(metrics.holder_address),
                       bytes_to_hex_str(metrics.token_address))
                result[key] = TokenHolderMetricsCurrentD(
                    holder_address=bytes_to_hex_str(metrics.holder_address),
                    token_address=bytes_to_hex_str(metrics.token_address),
                    block_number=metrics.block_number,
                    block_timestamp=int(metrics.block_timestamp.timestamp()),
                    first_block_timestamp=int(metrics.first_block_timestamp.timestamp()),
                    last_swap_timestamp=int(
                        metrics.last_swap_timestamp.timestamp()) if metrics.last_swap_timestamp else 0,
                    last_transfer_timestamp=int(
                        metrics.last_transfer_timestamp.timestamp()) if metrics.last_transfer_timestamp else 0,
                    current_balance=float(metrics.current_balance),
                    max_balance=float(metrics.max_balance),
                    total_buy_count=metrics.total_buy_count,
                    total_buy_amount=float(metrics.total_buy_amount),
                    total_buy_usd=float(metrics.total_buy_usd),
                    total_sell_count=metrics.total_sell_count,
                    total_sell_amount=float(metrics.total_sell_amount),
                    total_sell_usd=float(metrics.total_sell_usd),
                    swap_buy_count=metrics.swap_buy_count,
                    swap_buy_amount=float(metrics.swap_buy_amount),
                    swap_buy_usd=float(metrics.swap_buy_usd),
                    swap_sell_count=metrics.swap_sell_count,
                    swap_sell_amount=float(metrics.swap_sell_amount),
                    swap_sell_usd=float(metrics.swap_sell_usd),
                    success_sell_count=metrics.success_sell_count,
                    fail_sell_count=metrics.fail_sell_count,
                    current_average_buy_price=float(metrics.current_average_buy_price),
                    realized_pnl=float(metrics.realized_pnl),
                    win_rate=float(metrics.win_rate)
                )

        session.close()
        return result

    def _get_token_dex_prices_batch(self, token_blocks: list[tuple[str, int]]) -> dict[tuple[str, int], float]:
        result = {}
        if not token_blocks:
            return result

        token_addresses = [hex_str_to_bytes(token) for token in set(token for token, _ in token_blocks)]
        max_block = max(block for _, block in token_blocks)

        price_sql = text("""
            WITH ranked_prices AS (
                SELECT 
                    token_address,
                    token_price,
                    ROW_NUMBER() OVER (PARTITION BY token_address ORDER BY block_number DESC) AS rn
                FROM af_dex_block_token_price
                WHERE token_address in :token_addresses
                AND block_number <= :max_block
            )
            SELECT token_address, token_price
            FROM ranked_prices
            WHERE rn = 1
        """)

        session = self._service.get_service_session()
        prices = session.execute(
            price_sql,
            {
                'token_addresses': tuple(token_addresses),
                'max_block': max_block
            }
        ).fetchall()
        session.close()

        token_prices = {bytes_to_hex_str(price[0]): float(price[1]) for price in prices}

        for token_block in token_blocks:
            token_addr, _ = token_block
            result[token_block] = token_prices.get(token_addr, 0.0)

        return result
