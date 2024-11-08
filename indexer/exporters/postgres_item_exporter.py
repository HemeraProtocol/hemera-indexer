import logging
from datetime import datetime
from typing import Type

from dateutil.tz import tzlocal
from psycopg2.extras import execute_values
from tqdm import tqdm

from common.converter.pg_converter import domain_model_mapping
from common.models import HemeraModel
from indexer.exporters.base_exporter import BaseExporter, group_by_item_type
from indexer.utils.atomic_counter import AtomicCounter

logger = logging.getLogger(__name__)

COMMIT_BATCH_SIZE = 500


class TqdmExtraFormat(tqdm):
    """Provides both estimated and actual total time format parameters"""

    @property
    def format_dict(self):
        d = super().format_dict
        d.update(
            total_time=self.format_interval(d["total"] / (d["n"] / d["elapsed"]) if d["elapsed"] and d["n"] else 0),
            current_total_time=self.format_interval(d["elapsed"]),
        )
        return d


class PostgresItemExporter(BaseExporter):
    def __init__(self, service):
        self.service = service
        self.main_progress = None
        self.sub_progress = None

    def export_items(self, items, **kwargs):
        start_time = datetime.now(tzlocal())

        # Initialize main progress bar
        if kwargs.get("job_name"):
            job_name = kwargs.get("job_name")
            desc = f"{job_name}(PG)"
        else:
            desc = "Exporting items"
        self.main_progress = TqdmExtraFormat(
            total=len(items),
            desc=desc.ljust(35),
            unit="items",
            position=0,
            ncols=90,
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}] Est: {total_time}",
        )

        conn = self.service.get_conn()
        try:
            insert_stmt = ""
            items_grouped_by_type = group_by_item_type(items)
            tables = []

            # Process each item type
            for item_type in items_grouped_by_type.keys():
                item_group = items_grouped_by_type.get(item_type)

                if item_group:
                    pg_config = domain_model_mapping[item_type.__name__]
                    table = pg_config["table"]
                    do_update = pg_config["conflict_do_update"]
                    update_strategy = pg_config["update_strategy"]
                    converter = pg_config["converter"]

                    # Initialize sub-progress bar for current table
                    self.sub_progress = TqdmExtraFormat(
                        total=len(item_group),
                        desc=f"Processing {table.__tablename__}".ljust(35),
                        unit="items",
                        position=1,
                        leave=False,
                        ncols=90,
                        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
                    )

                    cur = conn.cursor()
                    data = []

                    # Process items with progress tracking
                    for item in item_group:
                        converted_item = converter(table, item, do_update)
                        data.append(converted_item)
                        self.sub_progress.update(1)
                        self.main_progress.update(1)

                    if data:
                        columns = list(data[0].keys())
                        values = [tuple(d.values()) for d in data]

                        insert_stmt = sql_insert_statement(table, do_update, columns, where_clause=update_strategy)

                        # Execute in batches with progress tracking
                        for i in range(0, len(values), COMMIT_BATCH_SIZE):
                            batch = values[i : i + COMMIT_BATCH_SIZE]
                            execute_values(cur, insert_stmt, batch)
                            conn.commit()

                    tables.append(table.__tablename__)
                    self.sub_progress.close()

        except Exception as e:
            logger.error(f"Error exporting items: {e}")
            logger.error(f"{insert_stmt}")
            raise Exception("Error exporting items")
        finally:
            self.service.release_conn(conn)
            if self.main_progress:
                self.main_progress.close()
            if self.sub_progress:
                self.sub_progress.close()

        end_time = datetime.now(tzlocal())


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
