import logging
from datetime import datetime

from sqlalchemy import text

from hemera.indexer.domains.block import Block
from hemera.indexer.jobs.base_job import ExtensionJob
from hemera_udf.token_price.domains import BlockTokenPrice

logger = logging.getLogger(__name__)


class ExportBlockTokenPriceJob(ExtensionJob):
    dependency_types = [Block]

    output_types = [BlockTokenPrice]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = kwargs["config"].get("db_service")
        config = kwargs["config"].get("export_block_token_price_job", {})
        self.symbols = set(config.values())
        pass

    @staticmethod
    def ts_to_date(ts):
        return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def date_to_ts(date):
        return int(date.timestamp())

    def _process(self, **kwargs):
        if not self.symbols:
            return

        blocks = self._data_buff[Block.type()]
        if not blocks:
            return
        blocks.sort(key=lambda block: block.number)

        start_block_timestamp = datetime.utcfromtimestamp(blocks[0].timestamp).strftime("%Y-%m-%d %H:%M:%S")
        end_block_timestamp = datetime.utcfromtimestamp(blocks[-1].timestamp).strftime("%Y-%m-%d %H:%M:%S")

        token_price_results = self.get_token_price(start_block_timestamp, end_block_timestamp)

        for block in blocks:
            price_map = {}

            for symbol in self.symbols:
                closest_price = None
                closest_time_diff = float("inf")

                for price in token_price_results:
                    if price.symbol == symbol:
                        time_diff = abs(price.timestamp.timestamp() - block.timestamp)
                        if time_diff < closest_time_diff:
                            closest_time_diff = time_diff
                            closest_price = float(price.price)

                price_map[symbol] = closest_price

                block_token_price = BlockTokenPrice(
                    token_symbol=symbol, token_price=price_map[symbol], block_number=block.number
                )
                self._collect_domain(block_token_price)
        pass

    def get_token_price(self, start_block_timestamp, end_block_timestamp):
        session = self._service.Session()

        sql = text(
            """
            select *
            from token_prices
            where symbol in :symbols
              and timestamp between :start_block_timestamp and :end_block_timestamp
        """
        )

        result = session.execute(
            sql,
            {
                "symbols": tuple(self.symbols),  # 将集合转成元组
                "start_block_timestamp": start_block_timestamp,
                "end_block_timestamp": end_block_timestamp,
            },
        )

        result_fetchall = result.fetchall()

        existing_symbols = {r.symbol for r in result_fetchall}
        missing_symbols = self.symbols - existing_symbols

        if missing_symbols:
            latest_symbol_sql = text(
                """
                WITH ranked_prices AS (
                    SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY timestamp DESC) AS row_num
                    FROM token_prices
                    WHERE symbol IN :symbols and timestamp < :end_block_timestamp
                )
                SELECT *
                FROM ranked_prices
                WHERE row_num = 1;
            """
            )

            latest_symbol_result = session.execute(
                latest_symbol_sql, {"symbols": tuple(missing_symbols), "end_block_timestamp": end_block_timestamp}
            )

            latest_symbol_result_fetchall = latest_symbol_result.fetchall()
            result_fetchall.extend(latest_symbol_result_fetchall)

        return result_fetchall
