import os
from contextlib import contextmanager

from alembic import command
from alembic.config import Config
from psycopg2 import pool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@contextmanager
def session_scope(session):
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class PostgreSQLService(object):
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance


    def __init__(self, jdbc_url, db_version="head", script_location="migrations", init_schema=True):
        self.db_version = db_version
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
        if init_schema:
            self.init_schema(script_location)

    def get_conn(self):
        return self.connection_pool.getconn()

    def release_conn(self, conn):
        self.connection_pool.putconn(conn)

    def init_schema(self, script_location):
        alembic_cfg = Config()
        # Set script location and version path separator
        alembic_cfg.set_main_option("script_location", script_location)
        alembic_cfg.set_main_option("version_path_separator", os.pathsep)

        # Set the database connection URL
        alembic_cfg.set_main_option("sqlalchemy.url", self.jdbc_url)

        # Configure log settings
        alembic_cfg.set_main_option("loggers", "root,sqlalchemy,alembic")
        alembic_cfg.set_main_option("handlers", "console")
        alembic_cfg.set_main_option("formatters", "generic")

        # Configure root logger
        alembic_cfg.set_section_option("logger_root", "level", "WARN")
        alembic_cfg.set_section_option("logger_root", "handlers", "console")
        alembic_cfg.set_section_option("logger_root", "qualname", "")

        # Configure SQLAlchemy logger
        alembic_cfg.set_section_option("logger_sqlalchemy", "level", "WARN")
        alembic_cfg.set_section_option("logger_sqlalchemy", "handlers", "")
        alembic_cfg.set_section_option("logger_sqlalchemy", "qualname", "sqlalchemy.engine")

        # Configure Alembic logger
        alembic_cfg.set_section_option("logger_alembic", "level", "INFO")
        alembic_cfg.set_section_option("logger_alembic", "handlers", "")
        alembic_cfg.set_section_option("logger_alembic", "qualname", "alembic")

        # Configure console handler
        alembic_cfg.set_section_option("handler_console", "class", "StreamHandler")
        alembic_cfg.set_section_option("handler_console", "args", "(sys.stderr,)")
        alembic_cfg.set_section_option("handler_console", "level", "NOTSET")
        alembic_cfg.set_section_option("handler_console", "formatter", "generic")

        command.upgrade(alembic_cfg, self.db_version)

    def get_service_uri(self):
        return self.jdbc_url

    def get_service_engine(self):
        return self.engine

    def get_service_session(self):
        return self.Session()

    def get_service_connection(self):
        return self.engine.connect()
