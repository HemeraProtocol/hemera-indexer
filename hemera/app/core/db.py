import os

from sqlmodel import create_engine


class Database:
    _read_engine = None
    _write_engine = None
    _common_engine = None

    @classmethod
    def get_read_engine(cls):
        if cls._read_engine is None:
            cls._read_engine = create_engine(
                os.getenv("READ_POSTGRES_URL") or os.getenv("POSTGRES_URL"),
                pool_pre_ping=True,  # TODO: Test Bugfix
            )
        return cls._read_engine

    @classmethod
    def get_write_engine(cls):
        if cls._write_engine is None:
            cls._write_engine = create_engine(os.getenv("WRITE_POSTGRES_URL") or os.getenv("POSTGRES_URL"))
        return cls._write_engine

    @classmethod
    def get_common_engine(cls):
        if cls._common_engine is None:
            cls._common_engine = create_engine(os.getenv("COMMON_POSTGRES_URL") or os.getenv("POSTGRES_URL"))
        return cls._common_engine
