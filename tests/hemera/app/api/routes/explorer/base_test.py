from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from hemera.app.main import app
from hemera.common.models.blocks import Blocks
from hemera.common.models.contracts import Contracts
from hemera.common.models.tokens import Tokens
from hemera.common.models.transactions import Transactions
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture(autouse=True)
def clean_db(session):
    """Clean database before each test"""
    # Order matters due to foreign key constraints
    session.exec(delete(Transactions))
    session.exec(delete(Contracts))
    session.exec(delete(Tokens))
    session.exec(delete(Blocks))

    session.commit()


@pytest.mark.serial
@pytest.fixture
def client(engine):
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.serial
@pytest.fixture
def sample_blocks(clean_db, session):
    """Create a set of test blocks"""
    blocks = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    # Create 10 consecutive blocks
    for i in range(10):
        block = Blocks(
            number=1000 + i,
            hash=f"0x{i:064x}".encode(),
            timestamp=base_time + timedelta(minutes=i),
        )
        blocks.append(block)
        session.add(block)

    session.commit()
    return blocks


@pytest.fixture
def sample_transactions(clean_db, session):
    """Create sample transactions for testing"""
    transactions = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    for i in range(5):
        tx = Transactions(
            hash=f"0x{i:064x}".encode(),
            block_number=1000 + i,
            from_address=f"0x{i:040x}".encode(),
            to_address=f"0x{i+1:040x}".encode(),
            value=1000000 * (i + 1),
            timestamp=base_time + timedelta(minutes=i),
        )
        transactions.append(tx)
        session.add(tx)

    session.commit()
    return transactions


@pytest.fixture
def sample_tokens(clean_db, session):
    """Create sample tokens for testing"""
    tokens = [
        Tokens(
            address=f"0x{i:040x}".encode(),
            name=f"Token{i}",
            symbol=f"TK{i}",
            decimals=18,
            icon_url=f"https://example.com/token{i}.png",
        )
        for i in range(3)
    ]

    for token in tokens:
        session.add(token)
    session.commit()
    return tokens


# Health Check Tests
@pytest.mark.serial
@pytest.mark.api
def test_health_check_success(client, session):
    """Test successful health check with single block"""
    test_block = Blocks(
        number=12345,
        hash=b"0x07e78dcf820fdee6bde4317a41e756acc281d328598183d0028e95f7f84d1bd8",
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
    )
    session.add(test_block)
    session.commit()

    response = client.get("/v1/explorer/health")

    assert response.status_code == 200
    data = response.json()

    assert data["latest_block_number"] == test_block.number
    assert data["latest_block_timestamp"] == test_block.timestamp.isoformat()
    assert data["status"] == "OK"

    # Verify database pool status
    assert "engine_pool_status" in data
    assert "read_pool_status" in data
    assert "write_pool_status" in data
    assert "common_pool_status" in data


@pytest.mark.serial
@pytest.mark.api
def test_health_check_no_blocks(client, session):
    """Test health check when no blocks exist"""
    session.exec(delete(Blocks))
    session.commit()

    response = client.get("/v1/explorer/health")

    assert response.status_code == 404
    assert response.json()["detail"] == "No blocks found"


# Stats Tests
@pytest.mark.serial
@pytest.mark.api
def test_get_stats_success(client, session, sample_blocks, sample_transactions):
    """Test successful stats retrieval"""

    response = client.get("/v1/explorer/stats")

    assert response.status_code == 200
    data = response.json()

    # Verify required fields
    assert "total_transactions" in data
    assert "transaction_tps" in data
    assert "latest_block" in data
    assert "avg_block_time" in data
    assert isinstance(data["total_transactions"], int)
    assert isinstance(data["transaction_tps"], float)


@pytest.mark.serial
@pytest.mark.api
def test_get_stats_no_blocks(client, session):
    """Test stats endpoint when no blocks exist"""

    session.exec(delete(Blocks))
    session.commit()

    response = client.get("/v1/explorer/stats")
    assert response.status_code == 404
    assert response.json()["detail"] == "No blocks found"


# Transactions Per Day Tests
@pytest.mark.serial
@pytest.mark.api
def test_transactions_per_day(client, session, sample_transactions):
    """Test transactions per day chart data"""
    response = client.get("/v1/explorer/charts/transactions_per_day")

    assert response.status_code == 200
    data = response.json()

    assert "title" in data
    assert "data" in data
    assert isinstance(data["data"], list)
    # Verify data structure
    if data["data"]:
        first_item = data["data"][0]
        assert "value" in first_item
        assert "count" in first_item


# Search Tests
@pytest.mark.serial
@pytest.mark.api
def test_search_by_block_number(client, session, sample_blocks):
    """Test search by block number"""
    block_number = 1000
    response = client.get(f"/v1/explorer/search?q={block_number}")

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["block_number"] == block_number


@pytest.mark.serial
@pytest.mark.api
def test_search_by_transaction_hash(client, session, sample_transactions):
    """Test search by transaction hash"""
    tx_hash = "0x0000000000000000000000000000000000000000000000000000000000000000"
    response = client.get(f"/v1/explorer/search?q={tx_hash}")

    assert response.status_code == 200
    results = response.json()
    if results:
        assert "transaction_hash" in results[0]


@pytest.mark.serial
@pytest.mark.api
def test_search_by_token(client, session, sample_tokens):
    """Test search by token name or symbol"""
    token_query = "Token"
    response = client.get(f"/v1/explorer/search?q={token_query}")

    assert response.status_code == 200
    results = response.json()

    for result in results:
        assert "token_name" in result
        assert "token_symbol" in result
        assert "token_address" in result


@pytest.mark.serial
@pytest.mark.api
def test_search_empty_query(client):
    """Test search with empty query"""
    response = client.get("/v1/explorer/search?q=")
    assert response.status_code == 422  # Validation error


@pytest.mark.serial
@pytest.mark.api
def test_search_invalid_address(client):
    """Test search with invalid ethereum address"""
    response = client.get("/v1/explorer/search?q=0xinvalid")
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.serial
@pytest.mark.api
def test_search_contract_address(client, session):
    """Test search by contract address"""
    # Create a test contract
    contract_address = "0x" + "1" * 40
    contract = Contracts(
        address=hex_str_to_bytes(contract_address), creator=hex_str_to_bytes("0x" + "2" * 40), created_at=datetime.now()
    )
    session.add(contract)
    session.commit()

    response = client.get(f"/v1/explorer/search?q={contract_address}")

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert "wallet_address" in results[0]


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
