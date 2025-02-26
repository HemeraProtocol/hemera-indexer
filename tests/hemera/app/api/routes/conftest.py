import os

import pytest
from fastapi.testclient import TestClient
from pytest_postgresql import factories
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, delete

from hemera.app.main import app
from hemera.common.models.address.address_internal_transaciton import AddressInternalTransactions
from hemera.common.models.blocks import Blocks
from hemera.common.models.contracts import Contracts
from hemera.common.models.tokens import Tokens
from hemera.common.models.traces import ContractInternalTransactions
from hemera.common.models.transactions import Transactions

postgresql_proc = factories.postgresql_proc()

postgresql = factories.postgresql("postgresql_proc")


@pytest.fixture(scope="function")
def engine(postgresql):
    """Create test database engine."""
    db_url = (
        f"postgresql://{postgresql.info.user}@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    os.environ["POSTGRES_URL"] = db_url

    engine = create_engine(db_url, pool_size=20, max_overflow=20, pool_timeout=30, pool_recycle=3600)

    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def session(engine):
    """Create a test session."""
    with Session(engine) as session:
        yield session
        session.rollback()


@pytest.fixture(autouse=True)
def clean_db(session):
    """Clean database before each test"""
    # Order matters due to foreign key constraints
    session.exec(delete(Transactions))
    session.exec(delete(Contracts))
    session.exec(delete(Tokens))
    session.exec(delete(Blocks))
    session.exec(delete(ContractInternalTransactions))
    session.exec(delete(AddressInternalTransactions))
    session.commit()


@pytest.fixture(scope="session", autouse=True)
def cleanup_postgresql(postgresql_proc):
    """Ensure proper cleanup of PostgreSQL process after all tests"""
    try:
        yield postgresql_proc
    finally:
        postgresql_proc.stop()


@pytest.mark.serial
@pytest.fixture
def client(engine):
    with TestClient(app) as test_client:
        yield test_client
