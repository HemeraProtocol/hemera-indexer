import collections
import logging
from datetime import datetime
from typing import List, Type

import sqlalchemy
from dateutil.tz import tzlocal
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from common.models import HemeraModel
from indexer.domain import Domain
from indexer.exporters.base_exporter import BaseExporter
from common.converter.pg_converter import domain_model_mapping

logger = logging.getLogger(__name__)


class PostgresItemExporter(BaseExporter):
    def __init__(self, service):

        self.service = service

    def export_items(self, items):
        start_time = datetime.now(tzlocal())

        session = self.service.get_service_session()
        try:
            items_grouped_by_type = group_by_item_type(items)
            tables = []
            for item_type in items_grouped_by_type.keys():
                item_group = items_grouped_by_type.get(item_type)

                if item_group:
                    pg_config = domain_model_mapping[item_type.__name__]

                    table = pg_config['table']
                    do_update = pg_config['conflict_do_update']
                    update_strategy = pg_config['update_strategy']
                    converter = pg_config['converter']

                    data = [converter(table, item, do_update) for item in item_group]

                    if do_update:
                        statement = insert(table).values(data)
                        statement = self.on_conflict_do_update(item_type, table, statement, update_strategy)
                        session.execute(statement)
                        session.commit()

                    else:
                        statement = insert(table).values(data).on_conflict_do_nothing()
                        session.execute(statement)
                        session.commit()

                    tables.append(table.__tablename__)

        except Exception as e:
            # print(e)
            logger.error(f"Error exporting items:{e}")
            # print(item_type, insert_stmt, [i[-1] for i in data])
            raise Exception("Error exporting items")
        finally:
            session.close()
        end_time = datetime.now(tzlocal())
        logger.info(
            "Exporting items to table {} end, Item count: {}, Took {}"
            .format(", ".join(tables), len(items), (end_time - start_time)))

    @staticmethod
    def on_conflict_do_update(domain: Type[Domain], model: Type[HemeraModel], statement, where_clause=None):
        pk_list = []
        for constraint in model._sa_registry.metadata.tables[model.__tablename__.lower()].constraints:
            if isinstance(constraint, sqlalchemy.schema.PrimaryKeyConstraint):
                for column in constraint.columns:
                    pk_list.append(column.name)

        update_set = {}
        for exc in statement.excluded:
            if exc.name not in pk_list and hasattr(domain, exc.name):
                update_set[exc.name] = exc

        if where_clause:
            where_clause = text(where_clause)

        statement = statement.on_conflict_do_update(index_elements=pk_list, set_=update_set, where=where_clause)
        return statement


def group_by_item_type(items: List[Domain]):
    result = collections.defaultdict(list)
    for item in items:
        key = item.__class__
        result[key].append(item)

    return result
