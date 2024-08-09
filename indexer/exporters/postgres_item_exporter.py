import logging
from datetime import datetime
from typing import Type

import sqlalchemy
from dateutil.tz import tzlocal
from psycopg2.extras import execute_values
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from common.converter.pg_converter import domain_model_mapping
from common.models import HemeraModel
from indexer.domain import Domain
from indexer.exporters.base_exporter import BaseExporter, group_by_item_type

logger = logging.getLogger(__name__)

COMMIT_BATCH_SIZE = 500


class PostgresItemExporter(BaseExporter):
    def __init__(self, service):

        self.service = service

    def export_items(self, items):
        start_time = datetime.now(tzlocal())

        conn = self.service.get_conn()
        try:
            items_grouped_by_type = group_by_item_type(items)
            tables = []
            for item_type in items_grouped_by_type.keys():
                item_group = items_grouped_by_type.get(item_type)

                if item_group:
                    pg_config = domain_model_mapping[item_type.__name__]

                    table = pg_config["table"]
                    do_update = pg_config["conflict_do_update"]
                    update_strategy = pg_config["update_strategy"]
                    converter = pg_config["converter"]

                    cur = conn.cursor()
                    data = [converter(table, item, do_update) for item in item_group]

                    columns = list(data[0].keys())
                    values = [tuple(d.values()) for d in data]

                    insert_stmt = self.sql_insert_statement(
                        item_type, table, do_update, columns, where_clause=update_strategy
                    )

                    execute_values(cur, insert_stmt, values, page_size=COMMIT_BATCH_SIZE)
                    conn.commit()
                    tables.append(table.__tablename__)

        except Exception as e:
            # print(e)
            logger.error(f"Error exporting items:{e}")
            # print(item_type, insert_stmt, [i[-1] for i in data])
            raise Exception("Error exporting items")
        finally:
            conn.close()
        end_time = datetime.now(tzlocal())
        logger.info(
            "Exporting items to table {} end, Item count: {}, Took {}".format(
                ", ".join(tables), len(items), (end_time - start_time)
            )
        )

    @staticmethod
    def sql_insert_statement(
        domain: Type[Domain], model: Type[HemeraModel], do_update: bool, columns, where_clause=None
    ):
        pk_list = []
        for constraint in model._sa_registry.metadata.tables[model.__tablename__.lower()].constraints:
            if isinstance(constraint, sqlalchemy.schema.PrimaryKeyConstraint):
                for column in constraint.columns:
                    pk_list.append(column.name)

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
