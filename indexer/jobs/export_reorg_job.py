import logging

from psycopg2.extras import execute_values

from common.converter.pg_converter import domain_model_mapping
from indexer.exporters.postgres_item_exporter import sql_insert_statement
from indexer.jobs.base_job import BaseJob

logger = logging.getLogger(__name__)


class ExportReorgJob(BaseJob):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._should_reorg = True

    def _process(self, **kwargs):
        block_number = int(kwargs["start_block"])
        conn = self._service.get_conn()
        cur = conn.cursor()

        for key in self._data_buff.keys():
            if len(self._data_buff[key]) > 0:
                items = self._data_buff[key]
                domain = type(items[0])
                if domain.__name__ not in domain_model_mapping:
                    continue

                pg_config = domain_model_mapping[domain.__name__]

                table = pg_config["table"]
                do_update = pg_config["conflict_do_update"]
                update_strategy = pg_config["update_strategy"]
                converter = pg_config["converter"]

                if not hasattr(table, "reorg"):
                    continue

                reorg_data = [converter(table, item, do_update) for item in items]

                columns = list(reorg_data[0].keys())
                values = [tuple(d.values()) for d in reorg_data]

                insert_stmt = sql_insert_statement(table, do_update, columns, where_clause=update_strategy)

                if table.__tablename__ != "blocks":
                    cur.execute(self._build_clean_sql(table.__tablename__, block_number))

                execute_values(cur, insert_stmt, values, page_size=500)

        conn.commit()
        self._data_buff.clear()

    @staticmethod
    def _build_clean_sql(table, block_number):
        return f"DELETE FROM {table} WHERE block_number={block_number} AND reorg=TRUE"
