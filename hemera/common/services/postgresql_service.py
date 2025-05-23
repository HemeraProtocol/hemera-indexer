import threading
from contextlib import contextmanager
from multiprocessing import current_process

from alembic import command
from alembic.config import Config
from psycopg2.pool import ThreadedConnectionPool
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool


class PostgreSQLService:
    """
    A thread-safe PostgreSQL service class that manages database connections and sessions.
    Implements singleton pattern per JDBC URL to avoid multiple connection pools to the same database.
    """

    _instances: dict = {}
    _initialized: dict = {}
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, jdbc_url: str, *args, **kwargs) -> "PostgreSQLService":
        """
        Ensures only one instance exists per progress and JDBC URL.
        """
        p_name = current_process().name

        if (p_name, jdbc_url) not in cls._instances:
            with cls._lock:
                if (p_name, jdbc_url) not in cls._instances:
                    instance = super().__new__(cls)
                    cls._instances[(p_name, jdbc_url)] = instance
        return cls._instances[(p_name, jdbc_url)]

    def __init__(
        self,
        jdbc_url: str,
        min_connections: int = 2,
        max_connections: int = 10,
        pool_size: int = 10,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,  # 30 minutes
        application_name: str = "postgresql_service",
        db_version: str = "head",
        script_location: str = "hemera/migrations",
        init_schema: bool = False,
    ):
        """
        Initialize the PostgreSQL service with connection pooling.
        """
        p_name = current_process().name
        if (p_name, jdbc_url) in self._initialized:
            return

        self.jdbc_url: str = jdbc_url
        self.db_version: str = db_version

        # Initialize SQLAlchemy engine with better defaults
        self.engine: Engine = create_engine(
            jdbc_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,
            connect_args={
                "application_name": application_name,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            },
        )

        # Initialize psycopg2 connection pool
        self.connection_pool: ThreadedConnectionPool = ThreadedConnectionPool(
            min_connections,
            max_connections,
            jdbc_url,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
            application_name=application_name,
        )

        # Initialize session factory
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

        if init_schema:
            self._init_schema(script_location)

        self._initialized[(p_name, jdbc_url)] = True

    def _init_schema(self, script_location: str) -> None:
        """
        Initialize database schema using Alembic migrations.
        """
        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", script_location)
        alembic_cfg.set_main_option("sqlalchemy.url", self.jdbc_url)

        # Configure logging
        self._configure_alembic_logging(alembic_cfg)

        command.upgrade(alembic_cfg, self.db_version)

    def _configure_alembic_logging(self, config: Config) -> None:
        """
        Configure Alembic logging settings.
        """
        config.set_main_option("loggers", "root,sqlalchemy,alembic")
        config.set_main_option("handlers", "console")
        config.set_main_option("formatters", "generic")

        # Logger configurations
        loggers = {
            "root": ("WARN", "console", ""),
            "sqlalchemy": ("WARN", "", "sqlalchemy.engine"),
            "alembic": ("INFO", "", "alembic"),
        }

        for logger, (level, handlers, qualname) in loggers.items():
            section = f"logger_{logger}"
            config.set_section_option(section, "level", level)
            config.set_section_option(section, "handlers", handlers)
            config.set_section_option(section, "qualname", qualname)

        # Configure console handler
        config.set_section_option("handler_console", "class", "StreamHandler")
        config.set_section_option("handler_console", "args", "(sys.stderr,)")
        config.set_section_option("handler_console", "level", "NOTSET")
        config.set_section_option("handler_console", "formatter", "generic")

    @contextmanager
    def session_scope(self) -> Session:
        """
        Provide a transactional scope around a series of operations.
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def connection_scope(self):
        """
        Provide a scope for raw database connection usage.
        """
        conn = self.connection_pool.getconn()
        try:
            yield conn
        finally:
            self.connection_pool.putconn(conn)

    @contextmanager
    def cursor_scope(self):
        """
        Provide a scope for cursor operations.
        """
        with self.connection_scope() as conn:
            with conn.cursor() as cursor:
                yield cursor

    def close(self) -> None:
        """
        Close all connections and clean up resources.
        """
        if hasattr(self, "connection_pool"):
            self.connection_pool.closeall()
        if hasattr(self, "engine"):
            self.engine.dispose()

    def __del__(self) -> None:
        """
        Ensure resources are cleaned up when the instance is deleted.
        """
        self.close()

    # Convenience methods for backward compatibility
    def get_service_uri(self) -> str:
        return self.jdbc_url

    def get_service_engine(self) -> Engine:
        return self.engine

    def get_service_session(self) -> Session:
        return self.Session()

    def get_conn(self):
        """
        @deprecated Use connection_scope instead
        """
        return self.connection_pool.getconn()

    def release_conn(self, conn) -> None:
        """
        @deprecated Use connection_scope instead
        """
        self.connection_pool.putconn(conn)
