from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from exporters.jdbc.schema.blocks import Blocks
from exporters.jdbc.schema.transactions import Transactions
from exporters.jdbc.schema.logs import Logs
from sqlalchemy.ext.declarative import declarative_base


class PostgreSQLService(object):
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, jdbc_url, init_mode=False):
        self.mode = init_mode
        self.engine = create_engine(jdbc_url)
        self.Session = sessionmaker(bind=self.engine)
        self.init_schema()

    def init_schema(self):
        if self.mode:
            Base = declarative_base()
            Base.metadata.drop_all(self.engine)

        Blocks.metadata.create_all(self.engine)
        Transactions.metadata.create_all(self.engine)
        Logs.metadata.create_all(self.engine)

    def get_service_engine(self):
        return self.engine

    def get_service_session(self):
        return self.Session()
