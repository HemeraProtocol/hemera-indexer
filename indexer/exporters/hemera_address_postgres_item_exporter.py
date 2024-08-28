import logging
from datetime import datetime
from typing import Type

import sqlalchemy
from dateutil.tz import tzlocal
from psycopg2.extras import execute_values

from common.converter.pg_converter import domain_model_mapping
from common.models import HemeraModel
from common.services.hemera_postgresql_service import HemeraPostgreSQLService
from common.services.postgresql_service import PostgreSQLService
from indexer.exporters.base_exporter import BaseExporter, group_by_item_type
from indexer.modules.custom.address_index.domain import *

logger = logging.getLogger(__name__)

COMMIT_BATCH_SIZE = 500


class HemeraAddressPostgresItemExporter(BaseExporter):
    hemera_output_types = [
        AddressTransaction,
        AddressNftTransfer,
        AddressTokenTransfer,
    ]

    def __init__(self, output, chain_id):
        url = output.replace("hemera_postgresql://", "postgresql://")
        service = HemeraPostgreSQLService(url)
        self.service = service
        self.chain_id = chain_id

    def export_items(self, items):
        start_time = datetime.now(tzlocal())

        conn = self.service.get_conn()
        try:
            items_grouped_by_type = group_by_item_type(items)
            tables = []
            for item_type in items_grouped_by_type.keys():
                if item_type not in self.hemera_output_types:
                    continue
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
                    values = [tuple(d.values()) + (self.chain_id,) for d in data]

                    insert_stmt = sql_insert_statement(table, do_update, columns, where_clause=update_strategy)

                    execute_values(cur, insert_stmt, values, page_size=COMMIT_BATCH_SIZE)
                    conn.commit()
                    tables.append(table.__tablename__)

        except Exception as e:
            # print(e)
            logger.error(f"Error exporting items:{e}")
            logger.error(f"{insert_stmt}")
            # print(item_type, insert_stmt, [i[-1] for i in data])
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
    columns = columns + ["chain_id"]
    for pk in model.__table__.primary_key.columns:
        pk_list.append(pk.name)
    pk_list.append("chain_id")

    update_list = list(set(columns) - set(pk_list))

    if do_update:
        insert_stmt = "INSERT INTO {}.hemera_{} ({}) VALUES %s ON CONFLICT ({}) DO UPDATE SET {}".format(
            model.schema(),
            model.__tablename__,
            ", ".join(columns),
            ", ".join(pk_list),
            ", ".join(["{} = EXCLUDED.{}".format(column, column) for column in update_list]),
        )
        if where_clause:
            insert_stmt += " WHERE {}".format(where_clause)
    else:
        insert_stmt = "INSERT INTO {}.hemera_{} ({}) VALUES %s ON CONFLICT DO NOTHING ".format(
            model.schema(),
            model.__tablename__,
            ", ".join(columns),
        )
    return insert_stmt
