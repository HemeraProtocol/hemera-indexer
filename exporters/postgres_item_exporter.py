import collections
import logging
from datetime import datetime

import sqlalchemy
from dateutil.tz import tzlocal
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from exporters.base_exporter import BaseExporter
from exporters.jdbc.converter.postgresql_model_converter import convert_item

logger = logging.getLogger(__name__)


class PostgresItemExporter(BaseExporter):
    def __init__(self, service):

        self.service = service
        self.conflict_do_update = {}

    def export_items(self, items):
        start_time = datetime.now(tzlocal())

        session = self.service.get_service_session()
        try:
            models, items_grouped_by_type = group_by_item_type(items)
            tables = []
            for item_type in items_grouped_by_type.keys():
                item_group = items_grouped_by_type.get(item_type)
                tables.append(models[item_type].__tablename__)

                if item_group:
                    self.check_update_strategy(item_group[0])
                    data = list(self.convert_items(item_type, item_group))
                    if item_type in self.conflict_do_update.keys():
                        statement = insert(models[item_type]).values(data)
                        statement = self.on_conflict_do_update(models[item_type], statement)
                        session.execute(statement)
                        session.commit()

                    else:
                        statement = insert(models[item_type]).values(data).on_conflict_do_nothing()
                        session.execute(statement)
                        session.commit()

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
    def convert_items(item_type, items):
        for item in items:
            yield convert_item(item_type, item)

    def check_update_strategy(self, data_example):
        if "update_strategy" in data_example:
            model = data_example["model"]
            self.conflict_do_update[model.__tablename__] = data_example["update_strategy"]

    def on_conflict_do_update(self, model, statement):
        pk_list = []
        for constraint in model._sa_registry.metadata.tables[model.__tablename__.lower()].constraints:
            if isinstance(constraint, sqlalchemy.schema.PrimaryKeyConstraint):
                for column in constraint.columns:
                    pk_list.append(column.name)

        update_set = {}
        for exc in statement.excluded:
            if exc.name not in pk_list:
                update_set[exc.name] = exc

        where_clause = None
        if model.__tablename__ in self.conflict_do_update:
            where_clause = text(self.conflict_do_update[model.__tablename__])

        statement = statement.on_conflict_do_update(index_elements=pk_list, set_=update_set, where=where_clause)
        return statement


def group_by_item_type(items):
    models = dict()
    result = collections.defaultdict(list)
    for item in items:
        key = item["model"].__tablename__
        models[key] = item["model"]
        result[key].append(item)

    return models, result
