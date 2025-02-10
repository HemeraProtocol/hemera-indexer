import logging
import time
from dataclasses import asdict

from sortedcontainers import SortedDict
from sqlalchemy import or_, text

from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from hemera.indexer.domains.token_transfer import ERC20TokenTransfer
from hemera.indexer.jobs.base_job import ExtensionJob
from hemera_udf.token_holder_metrics.domains.metrics import (
    TokenHolderMetricsCurrentD,
    TokenHolderMetricsHistoryD,
    TokenHolderTransferWithPriceD,
)
from hemera_udf.token_holder_metrics.models.metrics import TokenHolderMetricsCurrent
from hemera_udf.token_price.domains import DexBlockTokenPrice
from hemera_udf.uniswap_v2.domains import UniswapV2SwapEvent
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import UniswapV3SwapEvent

logger = logging.getLogger(__name__)

MAX_SAFE_VALUE = 2**255


class ExportTokenHolderMetricsJob(ExtensionJob):
    dependency_types = [ERC20TokenTransfer, UniswapV2SwapEvent, UniswapV3SwapEvent, DexBlockTokenPrice]
    output_types = [TokenHolderMetricsCurrentD, TokenHolderTransferWithPriceD, TokenHolderMetricsHistoryD]
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

        logger.info("Initializing history token prices...")
        self._init_history_token_prices(kwargs["start_block"])
        logger.info(f"History token prices initialized in {time.time() - start_time:.2f}s")

        logger.info("Initializing token dex prices batch...")
        t1 = time.time()
        self._init_token_dex_prices_batch(kwargs["start_block"], kwargs["end_block"])
        logger.info(f"Token dex prices initialized in {time.time() - t1:.2f}s")

        transfers = self._data_buff[ERC20TokenTransfer.type()]
        swaps = self._data_buff[UniswapV2SwapEvent.type()] + self._data_buff[UniswapV3SwapEvent.type()]
        swap_txs = {swap.transaction_hash: swap for swap in swaps}

        logger.info(f"Processing {len(transfers)} transfers and {len(swaps)} swaps...")
        t2 = time.time()
        transfers = sorted(
            [t for t in transfers if t.token_address not in self._non_meme_tokens],
            key=lambda x: (x.block_number, x.log_index),
        )
        logger.info(f"Filtered non-meme tokens in {time.time() - t2:.2f}s")

        t3 = time.time()
        transfer_metrics = []
        for i, transfer in enumerate(transfers):
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
                elif (hasattr(swap, "to_address") and swap.to_address == transfer.from_address) or (
                    hasattr(swap, "recipient") and swap.recipient == transfer.from_address
                ):
                    token_holder_from_metrics.is_swap = True
                if swap.sender == transfer.to_address:
                    token_holder_to_metrics.is_buy = True
                    token_holder_to_metrics.is_swap = True
                elif (hasattr(swap, "to_address") and swap.to_address == transfer.to_address) or (
                    hasattr(swap, "recipient") and swap.recipient == transfer.to_address
                ):
                    token_holder_to_metrics.is_swap = True
            price = self._get_token_dex_price(transfer.token_address, transfer.block_number)
            amount_usd = transfer.value * price / 10 ** token["decimals"]
            token_holder_from_metrics.price_usd = price
            token_holder_from_metrics.transfer_usd = amount_usd
            token_holder_to_metrics.price_usd = price
            token_holder_to_metrics.transfer_usd = amount_usd
            transfer_metrics.append(token_holder_from_metrics)
            transfer_metrics.append(token_holder_to_metrics)
        logger.info(f"Completed transfer processing in {time.time() - t3:.2f}s")

        t4 = time.time()
        address_token_pairs = set()
        for metrics in transfer_metrics:
            address_token_pairs.add((metrics.holder_address, metrics.token_address))
        logger.info(f"Created {len(address_token_pairs)} address-token pairs in {time.time() - t4:.2f}s")

        logger.info("Querying existing metrics...")
        t5 = time.time()
        query_results = self._get_address_token_holder_metrics_batch(list(address_token_pairs))
        current_metrics = query_results
        logger.info(f"Query completed in {time.time() - t5:.2f}s")

        t6 = time.time()
        for i, metrics in enumerate(transfer_metrics):
            token = self.tokens.get(metrics.token_address)
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

            # buy
            # update balance
            # update total buy count, amount, usd
            # update current average buy price
            # sell
            # set average buy price to 0 when balance is less than 0.00001
            # calculate pnl
            # update balance
            # update total sell count, amount, usd
            # update realized pnl
            # update success sell count
            # update fail sell count
            # update win rate
            if metrics.transfer_action == "in":
                new_balance = now_metrics.current_balance + metrics.transfer_amount
                if new_balance / 10 ** token["decimals"] > 0.00001:
                    new_average_buy_price = (
                        metrics.transfer_usd
                        + now_metrics.current_balance * now_metrics.current_average_buy_price / 10 ** token["decimals"]
                    ) / ((metrics.transfer_amount + now_metrics.current_balance) / 10 ** token["decimals"])
                else:
                    new_average_buy_price = 0

                now_metrics.current_balance = new_balance
                now_metrics.total_buy_count += 1
                now_metrics.total_buy_amount += metrics.transfer_amount
                now_metrics.total_buy_usd += metrics.transfer_usd
                now_metrics.current_average_buy_price = new_average_buy_price
            else:
                sell_amount = metrics.transfer_amount
                sell_price = metrics.price_usd

                if now_metrics.current_balance > 0:
                    sell_pnl = (
                        (sell_price - now_metrics.current_average_buy_price) * sell_amount / 10 ** token["decimals"]
                    )
                    now_metrics.sell_pnl += sell_pnl

                    now_metrics.realized_pnl = (
                        now_metrics.total_sell_usd
                        - now_metrics.total_buy_usd
                        + now_metrics.current_balance * metrics.price_usd / 10 ** token["decimals"]
                    )

                    if sell_price > now_metrics.current_average_buy_price:
                        now_metrics.success_sell_count += 1
                    else:
                        now_metrics.fail_sell_count += 1

                    total_sells = now_metrics.success_sell_count + now_metrics.fail_sell_count
                    if total_sells > 0:
                        now_metrics.win_rate = now_metrics.success_sell_count / total_sells

                now_metrics.current_balance -= sell_amount
                if now_metrics.current_balance / 10 ** token["decimals"] < 0.00001:
                    now_metrics.current_average_buy_price = 0

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

            now_metrics.last_transfer_timestamp = metrics.block_timestamp
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
        logger.info(f"Metrics update completed in {time.time() - t6:.2f}s")

        self._collect_domains(list(current_metrics.values()))
        history_metrics = [TokenHolderMetricsHistoryD(**asdict(metrics)) for metrics in current_metrics.values()]
        self._collect_domains(history_metrics)
        self._update_history_token_prices()

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
                    FROM af_token_holder_metrics_current_all_p{partition_idx}
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
                        )

        session.close()
        return result

    def _init_history_token_prices(self, start_block: int):
        if self.history_token_prices is not None:
            return
        session = self._service.get_service_session()
        token_blocks = session.execute(
            text(
                """
                SELECT token_address, block_number, token_price
                FROM (
                    SELECT token_address, block_number, token_price,
                           ROW_NUMBER() OVER (PARTITION BY token_address ORDER BY block_number DESC) as rn
                    FROM af_dex_block_token_price
                    WHERE block_number < :start_block
                ) t
                WHERE rn = 1
            """
            ),
            {"start_block": start_block},
        ).fetchall()
        session.close()
        self.history_token_prices = {bytes_to_hex_str(row[0]): float(row[2]) for row in token_blocks}

    def _init_token_dex_prices_batch(self, start_block: int, end_block: int):

        price_sql = text(
            """
            SELECT token_address, block_number, token_price
            FROM af_dex_block_token_price
            WHERE block_number BETWEEN :min_block AND :max_block
            ORDER BY block_number
            """
        )

        session = self._service.get_service_session()
        logger.info("fetching token prices from %s to %s", start_block, end_block)
        prices = session.execute(price_sql, {"min_block": start_block, "max_block": end_block}).fetchall()

        logger.info("fetch %s  token prices", len(prices))

        token_price_maps = {token: SortedDict() for token in self.history_token_prices}

        for token in self.history_token_prices:
            token_price_maps[token][0] = self.history_token_prices[token]

        for price_row in prices:
            token_addr = bytes_to_hex_str(price_row[0])
            if token_addr not in token_price_maps:
                token_price_maps[token_addr] = SortedDict()
            block_num = price_row[1]
            price = float(price_row[2])
            token_price_maps[token_addr][block_num] = price

        session.close()

        logger.info("Initialized %s tokens", len(token_price_maps))

        self.token_price_maps = token_price_maps

    def _get_token_dex_price(self, token_addr: str, block_num: int):
        price_map = self.token_price_maps.get(token_addr)
        if not price_map:
            return self.history_token_prices.get(token_addr, 0.0)

        keys = list(price_map.keys())
        idx = price_map.bisect_left(block_num)

        if idx == 0:
            return 0.0
        elif idx == len(keys):
            return price_map[keys[-1]]
        elif keys[idx] == block_num:
            return price_map[block_num]
        else:
            return price_map[keys[idx - 1]]

    def _update_history_token_prices(self):
        logger.info("Updating history token prices..., before: %s", len(self.history_token_prices))
        for token_addr, price_map in self.token_price_maps.items():
            if not price_map:
                continue
            latest_block = price_map.keys()[-1]
            latest_price = price_map[latest_block]

            self.history_token_prices[token_addr] = latest_price
        logger.info("Updated history token prices..., after: %s", len(self.history_token_prices))
