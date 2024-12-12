from psycopg2 import pool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class HemeraPostgreSQLService(object):
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, jdbc_url):
        self.engine = create_engine(
            jdbc_url,
            pool_size=10,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=60,
            connect_args={"application_name": "hemera_indexer"},
        )
        self.jdbc_url = jdbc_url
        self.connection_pool = pool.SimpleConnectionPool(1, 10, jdbc_url)

        self.Session = sessionmaker(bind=self.engine)

    def get_conn(self):
        return self.connection_pool.getconn()

    def release_conn(self, conn):
        self.connection_pool.putconn(conn)

    def get_service_engine(self):
        return self.engine

    def get_service_session(self):
        return self.Session()

    def get_service_connection(self):
        return self.engine.connect()
