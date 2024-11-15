import logging
from typing import Type

from psycopg2.extras import execute_values
from tqdm import tqdm

from common.converter.pg_converter import domain_model_mapping
from common.models import HemeraModel
from common.services.postgresql_service import PostgreSQLService
from indexer.exporters.base_exporter import BaseExporter, group_by_item_type

logger = logging.getLogger(__name__)

COMMIT_BATCH_SIZE = 1000


class PostgresItemExporter(BaseExporter):
    def __init__(self, **service):
        self.postgres_url = service["postgres_url"]
        self.db_version = service.get("db_version")
        self.init_schema = service.get("init_schema")
        # self.service = service

    def export_items(self, items, **kwargs):
        # Initialize main progress bar
        if kwargs.get("job_name"):
            job_name = kwargs.get("job_name")
            desc = f"{job_name}(PG)"
        else:
            desc = "Exporting items"
        service = PostgreSQLService(self.postgres_url, db_version=self.db_version, init_schema=self.init_schema)

        with service.cursor_scope() as cur:

            try:
                insert_stmt = ""
                items_grouped_by_type = group_by_item_type(items)
                tables = []

                # Process each item type
                for item_type in items_grouped_by_type.keys():
                    item_group = items_grouped_by_type.get(item_type)

                    if item_group:
                        pg_config = domain_model_mapping[item_type]
                        table = pg_config["table"]
                        do_update = pg_config["conflict_do_update"]
                        update_strategy = pg_config["update_strategy"]
                        converter = pg_config["converter"]

                        # Initialize sub-progress bar for current table
                        data = []
                        # Process items with progress tracking
                        for item in item_group:
                            converted_item = converter(table, item, do_update)
                            data.append(converted_item)

                        if data:
                            columns = list(data[0].keys())
                            values = [tuple(d.values()) for d in data]

                            insert_stmt = sql_insert_statement(table, do_update, columns, where_clause=update_strategy)

                            # Execute in batches with progress tracking
                            for i in range(0, len(values), COMMIT_BATCH_SIZE):
                                batch = values[i : i + COMMIT_BATCH_SIZE]
                                execute_values(cur, insert_stmt, batch)
                                cur.connection.commit()

                        tables.append(table.__tablename__)

            except Exception as e:
                logger.error(f"Error exporting items: {e}")
                logger.error(f"{insert_stmt}")
                pass
                # raise e


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
