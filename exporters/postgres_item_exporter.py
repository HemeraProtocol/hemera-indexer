import logging
import collections
from datetime import datetime
from dateutil.tz import tzlocal
from sqlalchemy.dialects.postgresql import insert
from enumeration.eth_type import EthDataType
from exporters.jdbc.schema.blocks import Blocks
from exporters.jdbc.schema.transactions import Transactions
from exporters.jdbc.schema.logs import Logs
from exporters.jdbc.postgresql_service import PostgreSQLService
from exporters.jdbc.converter.postgresql_model_converter import PostgreSQLModelConverter

logger = logging.getLogger(__name__)


class PostgresItemExporter:
    table_mapping = {
        EthDataType.BLOCK: Blocks,
        EthDataType.TRANSACTION: Transactions,
        EthDataType.LOG: Logs,
    }

    def __init__(self, connection_url, mode):

        self.service = PostgreSQLService(connection_url, mode)
        self.converter = PostgreSQLModelConverter()

    def get_session(self):
        return self.service.get_service_session()

    def open(self):
        pass

    def close(self):
        pass

    def export_items(self, items):
        start_time = datetime.now(tzlocal())

        session = self.get_session()
        try:
            items_grouped_by_type = group_by_item_type(items)
            for item_type in items_grouped_by_type.keys():

                model = self.table_mapping.get(item_type)
                if model is None:
                    raise Exception("Unknown item type")

                item_group = items_grouped_by_type.get(item_type)
                if item_group:
                    data = list(self.convert_items(item_type, item_group))
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
        # model = self.table_mapping.get(item_type)
        #
        # if model is None:
        #     raise Exception("Unknown item type")
        #
        # statement = insert(model).values(item).on_conflict_do_nothing()
        # session.execute(statement)
        pass

    def convert_items(self, item_type, items):
        for item in items:
            yield self.converter.convert_item(item_type, item)


def group_by_item_type(items):
    result = collections.defaultdict(list)
    for item in items:
        result[type(item).__name__].append(item)

    return result
