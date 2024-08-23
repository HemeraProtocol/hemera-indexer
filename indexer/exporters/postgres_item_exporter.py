import asyncio
import logging
import os
from datetime import datetime
from typing import Type

import sqlalchemy
from dateutil.tz import tzlocal
from psycopg2.extras import execute_values

from common.converter.pg_converter import domain_model_mapping
from common.models import HemeraModel
from indexer.exporters.base_exporter import BaseExporter, group_by_item_type

logger = logging.getLogger(__name__)

COMMIT_BATCH_SIZE = int(os.getenv("COMMIT_BATCH_SIZE", 500))


class PostgresItemExporter(BaseExporter):
    def __init__(self, service):

        self.service = service

    logger = logging.getLogger(__name__)

    def export_items(self, items):
        start_time = datetime.now(tzlocal())

        conn = self.service.get_conn()
        try:
            insert_stmt = ""
            items_grouped_by_type = group_by_item_type(items)

            async def process_item_group(item_type, item_group):
                table_start_time = datetime.now(tzlocal())
                if not item_group:
                    return None

                pg_config = domain_model_mapping[item_type.__name__]
                table = pg_config["table"]
                do_update = pg_config["conflict_do_update"]
                update_strategy = pg_config["update_strategy"]
                converter = pg_config["converter"]

                cur = conn.cursor()
                data = [converter(table, item, do_update) for item in item_group]

                columns = list(data[0].keys())
                values = [tuple(d.values()) for d in data]

                insert_stmt = sql_insert_statement(table, do_update, columns, where_clause=update_strategy)

                execute_values(cur, insert_stmt, values, page_size=COMMIT_BATCH_SIZE)
                conn.commit()
                table_end_time = datetime.now(tzlocal())
                logger.info(
                    "Exporting items to table {} end, Item count: {}, Took {}".format(
                        table.__tablename__, len(item_group), (table_end_time - table_start_time)
                    )
                )
                return table.__tablename__

            async def run_tasks():
                tasks = [
                    process_item_group(item_type, items_grouped_by_type.get(item_type))
                    for item_type in items_grouped_by_type.keys()
                ]
                return await asyncio.gather(*tasks)

            tables = asyncio.run(run_tasks())
            tables = [table for table in tables if table is not None]

        except Exception as e:
            logger.error(f"Error exporting items:{e}")
            logger.error(f"{insert_stmt}")
            raise Exception("Error exporting items")
        finally:
            self.service.release_conn(conn)

        end_time = datetime.now(tzlocal())
        logger.info(
            "Exporting items to table {} end, Item count: {}, Took {}".format(
                ", ".join(tables), len(items), (end_time - start_time)
            )
        )


def sql_insert_statement(model: Type[HemeraModel], do_update: bool, columns, where_clause=None):
    pk_list = []
    for pk in model.__table__.primary_key.columns:
        pk_list.append(pk.name)

    update_list = list(set(columns) - set(pk_list))

    if do_update:
        insert_stmt = "INSERT INTO {}.{} ({}) VALUES %s ON CONFLICT ({}) DO UPDATE SET {}".format(
            model.schema(),
            model.__tablename__,
            ", ".join(columns),
            ", ".join(pk_list),
            ", ".join(["{} = EXCLUDED.{}".format(column, column) for column in update_list]),
        )
        if where_clause:
            insert_stmt += " WHERE {}".format(where_clause)
    else:
        insert_stmt = "INSERT INTO {}.{} ({}) VALUES %s ON CONFLICT DO NOTHING ".format(
            model.schema(),
            model.__tablename__,
            ", ".join(columns),
        )
    return insert_stmt
