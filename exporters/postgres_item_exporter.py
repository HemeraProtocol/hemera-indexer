import collections
import logging
from datetime import datetime

import sqlalchemy
from dateutil.tz import tzlocal
from sqlalchemy.dialects.postgresql import insert

from exporters.jdbc.converter.postgresql_model_converter import PostgreSQLModelConverter
from exporters.jdbc.postgresql_service import PostgreSQLService

logger = logging.getLogger(__name__)


class PostgresItemExporter:
    def __init__(self, connection_url, config):
        version = config.get('db_version') if config.get('db_version') else "head"
        confirm = config.get('confirm') if config.get('confirm') else False

        self.service = PostgreSQLService(connection_url, version)
        self.converter = PostgreSQLModelConverter(confirm)
        self.confirm = confirm

    def open(self):
        pass

    def close(self):
        pass

    def export_items(self, items):
        start_time = datetime.now(tzlocal())

        session = self.service.get_service_session()
        try:
            models, items_grouped_by_type = group_by_item_type(items)
            for item_type in items_grouped_by_type.keys():
                item_group = items_grouped_by_type.get(item_type)
                if item_group:
                    data = list(self.convert_items(item_type, item_group))
                    if self.confirm is True:
                        statement = insert(models[item_type]).values(data)
                        statement = on_conflict_do_update(models[item_type], statement)
                        session.execute(statement)
                        session.commit()

                    else:
                        statement = insert(models[item_type]).values(data).on_conflict_do_nothing()
                        session.execute(statement)
                        session.commit()

        except Exception as e:
            print(e)
            # print(item_type, insert_stmt, [i[-1] for i in data])
            raise Exception("Error exporting items")
        finally:
            session.close()
        end_time = datetime.now(tzlocal())
        logger.info(
            "Exporting items to PostgreSQL end, Item count: {}, Took {}".format(len(items), (end_time - start_time)))

    def export_item(self, session, item_type, item):
        pass

    def convert_items(self, item_type, items):
        for item in items:
            yield self.converter.convert_item(item_type, item)


def group_by_item_type(items):
    models = dict()
    result = collections.defaultdict(list)
    for item in items:
        key = item["model"].__tablename__
        models[key] = item["model"]
        result[key].append(item)

    return models, result


def on_conflict_do_update(model, statement):
    pk_list = []
    for constraint in model._sa_registry.metadata.tables[model.__tablename__.lower()].constraints:
        if isinstance(constraint, sqlalchemy.schema.PrimaryKeyConstraint):
            for column in constraint.columns:
                pk_list.append(column.name)

    update_set = {}
    for exc in statement.excluded:
        if exc.name not in pk_list:
            update_set[exc.name] = exc

    statement = statement.on_conflict_do_update(index_elements=pk_list, set_=update_set)
    return statement
