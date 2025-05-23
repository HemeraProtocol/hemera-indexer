import logging
import time
from dataclasses import asdict

from sqlalchemy import text

from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from hemera.indexer.jobs.base_job import ExtensionJob
from hemera_udf.token_holder_metrics.domains.metrics import (
    ERC20TokenTransferWithPriceD,
    TokenHolderMetricsCurrentD,
    TokenHolderMetricsHistoryD,
)
from hemera_udf.token_holder_metrics.models.metrics import TokenHolderMetricsCurrent

logger = logging.getLogger(__name__)

MAX_SAFE_VALUE = 2**255
MIN_BALANCE_THRESHOLD = 1e-4


class ExportTokenHolderMetricsJob(ExtensionJob):
    dependency_types = [ERC20TokenTransferWithPriceD]
    output_types = [TokenHolderMetricsCurrentD, TokenHolderMetricsHistoryD]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = kwargs["config"].get("db_service")
        self._non_meme_tokens = self._load_non_meme_tokens()
        self.history_token_prices = None

    def _collect(self, **kwargs):
        pass

    def _load_non_meme_tokens(self):
        session = self._service.get_service_session()
        non_meme_tokens = set(
            bytes_to_hex_str(row[0]) for row in session.execute(text("SELECT address FROM non_meme_tokens")).fetchall()
        )
        session.close()
        return non_meme_tokens

    def _process(self, **kwargs):
        start_time = time.time()

        transfers = self._data_buff[ERC20TokenTransferWithPriceD.type()]

        t2 = time.time()
        transfers = sorted(
            [t for t in transfers if t.token_address not in self._non_meme_tokens],
            key=lambda x: (x.block_number, x.log_index),
        )
        logger.info(f"Filtered non-meme tokens in {time.time() - t2:.2f}s")

        self._block_address_token_values = {}
        self._block_address_token_balances = {}
        for transfer in transfers:
            block_number = transfer.block_number
            from_key = (block_number, transfer.from_address, transfer.token_address)
            to_key = (block_number, transfer.to_address, transfer.token_address)

            if from_key not in self._block_address_token_values:
                self._block_address_token_values[from_key] = 0
            self._block_address_token_values[from_key] -= transfer.value

            if to_key not in self._block_address_token_values:
                self._block_address_token_values[to_key] = 0
            self._block_address_token_values[to_key] += transfer.value

            self._block_address_token_balances[from_key] = transfer.from_address_balance
            self._block_address_token_balances[to_key] = transfer.to_address_balance

        t3 = time.time()
        address_token_pairs = set()
        for transfer in transfers:
            if transfer.value > MAX_SAFE_VALUE:
                logger.warning(
                    f"Skipping transfer with unusually large value: {getattr(transfer, 'value', 'N/A')}, "
                    f"tx: {getattr(transfer, 'transaction_hash', 'N/A')}, "
                    f"token: {getattr(transfer, 'token_address', 'N/A')}"
                )
                continue
            token = self.tokens.get(transfer.token_address)
            if not token:
                logger.warning(f"Token {transfer.token_address} not found")
                continue

            # Add both from and to addresses to the set
            address_token_pairs.add((transfer.from_address, transfer.token_address))
            address_token_pairs.add((transfer.to_address, transfer.token_address))

        logger.info(f"Created {len(address_token_pairs)} address-token pairs in {time.time() - t3:.2f}s")

        logger.info("Querying existing metrics...")
        t5 = time.time()
        current_metrics = self._get_address_token_holder_metrics_batch(list(address_token_pairs))
        logger.info(f"Query completed in {time.time() - t5:.2f}s")

        t6 = time.time()
        for transfer in transfers:
            if transfer.value > MAX_SAFE_VALUE or transfer.token_address not in self.tokens:
                continue

            token = self.tokens[transfer.token_address]
            amount_usd = transfer.value * transfer.price / 10 ** (token["decimals"] or 0)

            # Process "from" address
            self._update_holder_metrics(
                current_metrics,
                transfer.from_address,
                transfer.token_address,
                transfer,
                "out",
                amount_usd,
                transfer.price,
                token,
            )

            # Process "to" address
            self._update_holder_metrics(
                current_metrics,
                transfer.to_address,
                transfer.token_address,
                transfer,
                "in",
                amount_usd,
                transfer.price,
                token,
            )

        for metrics in current_metrics.values():
            metrics.current_balance = self._block_address_token_balances.get(
                (metrics.block_number, metrics.holder_address, metrics.token_address), 0
            )

        logger.info(f"Metrics update completed in {time.time() - t6:.2f}s")

        self._collect_items(TokenHolderMetricsCurrentD.type(), list(current_metrics.values()))
        history_metrics = [TokenHolderMetricsHistoryD(**asdict(metrics)) for metrics in current_metrics.values()]
        self._collect_items(TokenHolderMetricsHistoryD.type(), history_metrics)

        total_time = time.time() - start_time
        logger.info(f"Total processing time: {total_time:.2f}s")

    def _get_address_token_holder_metrics_batch(
        self, address_token_pairs: list[tuple[str, str]]
    ) -> dict[tuple[str, str], TokenHolderMetricsCurrentD]:
        if not address_token_pairs:
            return {}

        start_time = time.time()
        logger.info(f"Starting to process {len(address_token_pairs)} address-token pairs")

        BATCH_SIZE = 1000
        result = {}
        session = self._service.get_service_session()

        partition_groups = {}
        for addr, token in address_token_pairs:
            first_char = int(addr[2:3], 16)
            partition_idx = first_char
            partition_groups.setdefault(partition_idx, []).append((addr, token))

        for partition_idx, partition_pairs in partition_groups.items():
            logger.info(f"Processing partition {partition_idx} with {len(partition_pairs)} pairs")

            for i in range(0, len(partition_pairs), BATCH_SIZE):
                batch_pairs = partition_pairs[i : i + BATCH_SIZE]

                address_bytes_pairs = [(hex_str_to_bytes(addr), hex_str_to_bytes(token)) for addr, token in batch_pairs]

                query = text(
                    f"""
                    SELECT *
                    FROM af_token_holder_metrics_current_p{partition_idx}
                    WHERE (holder_address, token_address) IN :pairs
                """
                )

                batch_results = (
                    session.query(TokenHolderMetricsCurrent)
                    .from_statement(query.params(pairs=tuple(address_bytes_pairs)))
                    .all()
                )

                pair_lookup = {
                    (bytes_to_hex_str(m.holder_address), bytes_to_hex_str(m.token_address)): m for m in batch_results
                }

                for addr, token in batch_pairs:
                    metrics = pair_lookup.get((addr, token))
                    if metrics:
                        result[(addr, token)] = TokenHolderMetricsCurrentD(
                            holder_address=addr,
                            token_address=token,
                            block_number=metrics.block_number,
                            block_timestamp=int(metrics.block_timestamp.timestamp()) if metrics.block_timestamp else 0,
                            first_block_timestamp=(
                                int(metrics.first_block_timestamp.timestamp()) if metrics.first_block_timestamp else 0
                            ),
                            last_swap_timestamp=(
                                int(metrics.last_swap_timestamp.timestamp()) if metrics.last_swap_timestamp else 0
                            ),
                            last_transfer_timestamp=(
                                int(metrics.last_transfer_timestamp.timestamp())
                                if metrics.last_transfer_timestamp
                                else 0
                            ),
                            current_balance=float(metrics.current_balance or 0),
                            max_balance=float(metrics.max_balance or 0),
                            max_balance_timestamp=(
                                int(metrics.max_balance_timestamp.timestamp()) if metrics.max_balance_timestamp else 0
                            ),
                            sell_25_timestamp=(
                                int(metrics.sell_25_timestamp.timestamp()) if metrics.sell_25_timestamp else 0
                            ),
                            sell_50_timestamp=(
                                int(metrics.sell_50_timestamp.timestamp()) if metrics.sell_50_timestamp else 0
                            ),
                            total_buy_count=metrics.total_buy_count or 0,
                            total_buy_amount=float(metrics.total_buy_amount or 0),
                            total_buy_usd=float(metrics.total_buy_usd or 0),
                            total_sell_count=metrics.total_sell_count or 0,
                            total_sell_amount=float(metrics.total_sell_amount or 0),
                            total_sell_usd=float(metrics.total_sell_usd or 0),
                            swap_buy_count=metrics.swap_buy_count or 0,
                            swap_buy_amount=float(metrics.swap_buy_amount or 0),
                            swap_buy_usd=float(metrics.swap_buy_usd or 0),
                            swap_sell_count=metrics.swap_sell_count or 0,
                            swap_sell_amount=float(metrics.swap_sell_amount or 0),
                            swap_sell_usd=float(metrics.swap_sell_usd or 0),
                            success_sell_count=metrics.success_sell_count or 0,
                            fail_sell_count=metrics.fail_sell_count or 0,
                            current_average_buy_price=float(metrics.current_average_buy_price or 0),
                            realized_pnl=float(metrics.realized_pnl or 0),
                            sell_pnl=float(metrics.sell_pnl or 0),
                            win_rate=float(metrics.win_rate or 0),
                            pnl_valid=bool(metrics.pnl_valid or False),
                        )

        session.close()
        return result

    def _update_holder_metrics(
        self,
        current_metrics: dict,
        holder_address: str,
        token_address: str,
        transfer,
        transfer_action: str,
        amount_usd: float,
        token_price: float,
        token: dict,
    ):
        key = (holder_address, token_address)

        if not current_metrics.get(key):
            current_metrics[key] = TokenHolderMetricsCurrentD(
                holder_address=holder_address,
                token_address=token_address,
                block_number=transfer.block_number,
                block_timestamp=transfer.block_timestamp,
                first_block_timestamp=transfer.block_timestamp,
                last_swap_timestamp=transfer.block_timestamp,
                last_transfer_timestamp=transfer.block_timestamp,
                pnl_valid=False,
            )

        metrics = current_metrics[key]
        if metrics.block_number > transfer.block_number:
            return

        metrics.block_number = transfer.block_number
        metrics.block_timestamp = transfer.block_timestamp

        set_pnl_valid_block_number = 0

        new_current_balance = (
            self._block_address_token_balances.get((transfer.block_number, holder_address, token_address), 0) or 0
        )

        if not metrics.pnl_valid:
            block_key = (transfer.block_number, holder_address, token_address)
            total_value = self._block_address_token_values.get(block_key, 0)

            if (
                abs(total_value - new_current_balance) < MIN_BALANCE_THRESHOLD
                or new_current_balance < MIN_BALANCE_THRESHOLD
            ):
                metrics.pnl_valid = True
                set_pnl_valid_block_number = transfer.block_number

        # buy
        # update balance
        # update total buy count, amount, usd
        # update current average buy price
        # sell
        # set average buy price to 0 when balance is less than MIN_BALANCE_THRESHOLD
        # calculate pnl
        # update balance
        # update total sell count, amount, usd
        # update realized pnl
        # update success sell count
        # update fail sell count
        # update win rate
        if transfer_action == "in":
            new_balance = metrics.current_balance + transfer.value
            if new_balance / 10 ** token["decimals"] > MIN_BALANCE_THRESHOLD:
                new_average_buy_price = (
                    amount_usd + metrics.current_balance * metrics.current_average_buy_price / 10 ** token["decimals"]
                ) / ((transfer.value + metrics.current_balance) / 10 ** token["decimals"])
            else:
                new_average_buy_price = 0

            metrics.current_balance = new_balance
            metrics.total_buy_count += 1
            metrics.total_buy_amount += transfer.value
            metrics.total_buy_usd += amount_usd
            metrics.current_average_buy_price = new_average_buy_price
        else:
            sell_amount = transfer.value

            if metrics.current_balance > 0:
                sell_pnl = (token_price - metrics.current_average_buy_price) * sell_amount / 10 ** token["decimals"]
                metrics.sell_pnl += sell_pnl

                metrics.realized_pnl = (
                    metrics.total_sell_usd
                    - metrics.total_buy_usd
                    + metrics.current_balance * token_price / 10 ** token["decimals"]
                )

                if token_price > metrics.current_average_buy_price:
                    metrics.success_sell_count += 1
                else:
                    metrics.fail_sell_count += 1

                total_sells = metrics.success_sell_count + metrics.fail_sell_count
                if total_sells > 0:
                    metrics.win_rate = metrics.success_sell_count / total_sells

            metrics.current_balance -= sell_amount
            if metrics.current_balance / 10 ** token["decimals"] < MIN_BALANCE_THRESHOLD:
                metrics.current_average_buy_price = 0

            metrics.total_sell_count += 1
            metrics.total_sell_amount += sell_amount
            metrics.total_sell_usd += amount_usd

        if metrics.current_balance >= metrics.max_balance:
            metrics.max_balance = metrics.current_balance
            metrics.max_balance_timestamp = metrics.block_timestamp
            metrics.sell_25_timestamp = 0
            metrics.sell_50_timestamp = 0

        if metrics.current_balance <= metrics.max_balance * 0.75 and metrics.sell_25_timestamp == 0:
            metrics.sell_25_timestamp = metrics.block_timestamp
        if metrics.current_balance <= metrics.max_balance * 0.5 and metrics.sell_50_timestamp == 0:
            metrics.sell_50_timestamp = metrics.block_timestamp

        metrics.last_transfer_timestamp = metrics.block_timestamp
        metrics.last_price = token_price
        if transfer.is_swap:
            metrics.last_swap_timestamp = metrics.block_timestamp

            if transfer_action == "in":
                metrics.swap_buy_count += 1
                metrics.swap_buy_amount += transfer.value
                metrics.swap_buy_usd += amount_usd
            else:
                metrics.swap_sell_count += 1
                metrics.swap_sell_amount += transfer.value
                metrics.swap_sell_usd += amount_usd

        if not metrics.pnl_valid or metrics.block_number == set_pnl_valid_block_number:
            metrics.sell_pnl = 0
            metrics.realized_pnl = 0
            metrics.success_sell_count = 0
            metrics.fail_sell_count = 0
            metrics.win_rate = 0
            metrics.current_average_buy_price = 0
            if metrics.block_number == set_pnl_valid_block_number and new_current_balance > MIN_BALANCE_THRESHOLD:
                metrics.current_average_buy_price = token_price
