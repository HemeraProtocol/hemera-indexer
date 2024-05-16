import logging
import collections
from datetime import datetime
from dateutil.tz import tzlocal
from sqlalchemy.dialects.postgresql import insert
from exporters.jdbc.schema.block_timestamp_mapper import BlockTimestampMapper
from exporters.jdbc.schema.blocks import Blocks
from exporters.jdbc.schema.transactions import Transactions
from exporters.jdbc.schema.logs import Logs
from exporters.jdbc.postgresql_service import PostgreSQLService
from exporters.jdbc.converter.postgresql_model_converter import PostgreSQLModelConverter

logger = logging.getLogger(__name__)


class PostgresItemExporter:
    table_mapping = {
        "blocks": Blocks,
        "transactions": Transactions,
        "logs": Logs,
        "block_ts_mapper": BlockTimestampMapper,
    }

    index_mapping = {
        "blocks": ['hash'],
        "transactions": ['hash'],
        "logs": ['log_index', 'block_hash', 'transaction_hash']
    }

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
            items_grouped_by_type = group_by_item_type(items)
            for item_type in items_grouped_by_type.keys():

                model = self.table_mapping.get(item_type)
                if model is None:
                    raise Exception("Unknown item type")

                item_group = items_grouped_by_type.get(item_type)
                if item_group:
                    data = list(self.convert_items(item_type, item_group))
                    if self.confirm is True:
                        for sub_data in data:
                            statement = insert(model).values(sub_data).on_conflict_do_update(
                                index_elements=self.index_mapping.get(item_type), set_=sub_data)
                            session.execute(statement)
                            session.commit()
                    else:
                        statement = insert(model).values(data).on_conflict_do_nothing()
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
    result = collections.defaultdict(list)
    for item in items:
        result[item["model"]].append(item)

    return result
