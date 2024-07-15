from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class PostgreSQLService(object):
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, jdbc_url, db_version="head"):
        self.db_version = db_version
        self.engine = create_engine(jdbc_url,
                                    pool_size=10,
                                    max_overflow=10,
                                    pool_timeout=30,
                                    pool_recycle=60,
                                    connect_args={
                                        "application_name": "hemera_indexer"
                                    })

        self.Session = sessionmaker(bind=self.engine)
        self.init_schema()

    def init_schema(self):
        alembic_config = Config("resource/hemera.ini")

        if self.db_version == "base":
            command.downgrade(alembic_config, "base")
        command.upgrade(alembic_config, self.db_version)

    def get_service_engine(self):
        return self.engine

    def get_service_session(self):
        return self.Session()
