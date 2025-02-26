#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/24 16:02
# @Author  ideal93
# @File  block_test.py.py
# @Brief

from datetime import datetime, timedelta

import pytest

from hemera.app.api.routes.helper.block import _get_blocks_by_condition
from hemera.common.models.blocks import Blocks


@pytest.mark.serial
@pytest.fixture
def sample_blocks(clean_db, session):
    """Create a set of test blocks including some reorged blocks"""
    blocks = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    # Create 10 consecutive blocks
    for i in range(10):
        block = Blocks(
            number=1000 + i,
            hash=bytes.fromhex(f"{i:064x}"),
            timestamp=base_time + timedelta(minutes=i),
            parent_hash=bytes.fromhex(f"{i-1:064x}") if i > 0 else bytes(32),
            gas_limit="15000000",
            gas_used=f"{5000000 + i * 100000}",
            base_fee_per_gas="1000000000",
            miner=bytes.fromhex(f"{i:040x}"),
            transactions_count=0,
            internal_transactions_count=0,
            reorg=False,
        )
        if i == 4:
            block.transactions_count = 1
        blocks.append(block)
        session.add(block)

    reorg_blocks = [
        Blocks(
            number=1002,
            hash=bytes.fromhex("deadbeef".ljust(64, "0")),
            timestamp=base_time + timedelta(minutes=2),
            parent_hash=bytes.fromhex(f"{1:064x}"),
            gas_limit="15000000",
            gas_used="5200000",
            base_fee_per_gas="1000000000",
            miner=bytes.fromhex("abc".ljust(40, "0")),
            transactions_count=0,
            internal_transactions_count=0,
            reorg=True,
        ),
        Blocks(
            number=1003,
            hash=bytes.fromhex("deadbeef2".ljust(64, "0")),
            timestamp=base_time + timedelta(minutes=3),
            parent_hash=bytes.fromhex("deadbeef".ljust(64, "0")),
            gas_limit="15000000",
            gas_used="5300000",
            base_fee_per_gas="1000000000",
            miner=bytes.fromhex("def".ljust(40, "0")),
            transactions_count=0,
            internal_transactions_count=0,
            reorg=True,
        ),
    ]

    for block in reorg_blocks:
        session.add(block)
        blocks.append(block)

    session.commit()

    return blocks


@pytest.mark.serial
@pytest.mark.api
def test_get_blocks_success(client, sample_blocks, session):
    """Test successful retrieval of blocks with default pagination"""
    response = client.get("/v1/explorer/blocks")

    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 1
    assert data["size"] == 25
    assert data["total"] == 1009  # highest block number
    assert len(data["data"]) == 10  # number of sample blocks

    # Verify first block data
    first_block = data["data"][0]
    assert first_block["number"] == 1009
    assert first_block["hash"] == "0x" + "0" * 63 + "9"
    assert "timestamp" in first_block
    assert first_block["transaction_count"] == 0
    assert first_block["internal_transaction_count"] == 0


@pytest.mark.serial
@pytest.mark.api
def test_get_blocks_with_pagination(client, sample_blocks, session):
    """Test blocks retrieval with custom pagination"""
    response = client.get("/v1/explorer/blocks?page=2&size=5")

    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 2
    assert data["size"] == 5
    assert len(data["data"]) == 5

    # Verify block numbers are in descending order
    block_numbers = [block["number"] for block in data["data"]]
    assert block_numbers == [1004, 1003, 1002, 1001, 1000]


@pytest.mark.serial
@pytest.mark.api
def test_get_blocks_with_transactions(client, sample_blocks, session):
    """Test blocks retrieval with transaction counts"""
    response = client.get("/v1/explorer/blocks")

    assert response.status_code == 200
    data = response.json()

    # Find a block that should have a transaction
    block_with_tx = next(block for block in data["data"] if block["number"] == 1004)

    assert block_with_tx["transaction_count"] == 1
    assert block_with_tx["internal_transaction_count"] == 0


@pytest.mark.serial
@pytest.mark.api
def test_get_blocks_invalid_pagination(client, sample_blocks):
    """Test blocks retrieval with invalid pagination parameters"""
    # Test negative page
    response = client.get("/v1/explorer/blocks?page=0")
    assert response.status_code == 422

    # Test negative size
    response = client.get("/v1/explorer/blocks?size=0")
    assert response.status_code == 422


@pytest.mark.serial
@pytest.mark.api
def test_get_blocks_empty_db(client, clean_db):
    """Test blocks retrieval with empty database"""
    response = client.get("/v1/explorer/blocks")

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert len(data["data"]) == 0
    assert data["page"] == 1
    assert data["size"] == 25


@pytest.mark.serial
@pytest.mark.api
def test_get_blocks_response_structure(client, sample_blocks):
    """Test the structure of block response data"""
    response = client.get("/v1/explorer/blocks")

    assert response.status_code == 200
    data = response.json()

    # Check first block has all required fields
    first_block = data["data"][0]
    required_fields = {
        "hash",
        "number",
        "timestamp",
        "parent_hash",
        "gas_limit",
        "gas_used",
        "base_fee_per_gas",
        "miner",
        "transaction_count",
        "internal_transaction_count",
    }

    assert all(field in first_block for field in required_fields)
    assert isinstance(first_block["number"], int)
    assert isinstance(first_block["hash"], str)
    assert isinstance(first_block["transaction_count"], int)


def test_get_blocks_exclude_reorg(session, sample_blocks):
    blocks = _get_blocks_by_condition(session, filter_condition=Blocks.reorg == False)

    assert len(blocks) == 10
    assert all(not block.reorg for block in blocks)

    blocks_at_1002 = _get_blocks_by_condition(
        session, filter_condition=(Blocks.number == 1002) & (Blocks.reorg == False)
    )
    assert len(blocks_at_1002) == 1
    assert not blocks_at_1002[0].reorg
    assert blocks_at_1002[0].hash != ("0x" + "deadbeef".ljust(64, "0")).encode()


def test_blocks_api_exclude_reorg(client, session, sample_blocks):
    response = client.get("/v1/explorer/blocks?page=1&size=10")
    assert response.status_code == 200
    data = response.json()

    assert len(data["data"]) == 10
    assert data["page"] == 1
    assert data["size"] == 10
    assert data["total"] == 1009

    block_numbers = [block["number"] for block in data["data"]]
    assert 1002 in block_numbers

    block_1002 = next(block for block in data["data"] if block["number"] == 1002)
    assert block_1002["hash"] != "0x" + "deadbeef".ljust(64, "0")


@pytest.fixture
def sample_blocks_details(clean_db, session):
    """Create sample blocks for testing block detail API

    Creates:
    - A sequence of 3 blocks with different timestamps
    - A special block with known hash for testing hash-based queries
    """
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    blocks = []

    # Create regular blocks
    for i in range(3):
        block = Blocks(
            number=1000 + i,
            hash=bytes.fromhex(f"{i:064x}"),
            parent_hash=bytes.fromhex(f"{i-1:064x}") if i > 0 else bytes(32),
            timestamp=base_time + timedelta(seconds=12 * i),
            gas_limit="15000000",
            gas_used=f"{5000000 + i * 100000}",
            base_fee_per_gas="1000000000",
            miner=bytes.fromhex(f"{i:040x}"),
            transactions_count=i,  # Different tx counts
            internal_transactions_count=i * 2,  # Different internal tx counts
            reorg=False,
        )
        blocks.append(block)
        session.add(block)

    # Create a block with known hash for testing
    known_hash = "deadbeef" * 8  # 32 bytes
    special_block = Blocks(
        number=2000,
        hash=bytes.fromhex(known_hash),
        parent_hash=bytes.fromhex("f" * 64),
        timestamp=base_time + timedelta(minutes=5),
        gas_limit="15000000",
        gas_used="5000000",
        base_fee_per_gas="1000000000",
        miner=bytes.fromhex("a" * 40),
        transactions_count=10,
        internal_transactions_count=5,
        reorg=False,
    )
    blocks.append(special_block)
    session.add(special_block)

    session.commit()
    return blocks


def test_get_block_detail_by_number(client, session, sample_blocks_details):
    """Test getting block details using block number"""
    response = client.get("/v1/explorer/block/1001")
    assert response.status_code == 200

    data = response.json()
    assert data["number"] == 1001
    assert data["transaction_count"] == 1
    assert data["internal_transaction_count"] == 2
    assert data["seconds_since_last_block"] == 12.0
    assert not data["is_last_block"]


def test_get_block_detail_by_hash(client, session, sample_blocks_details):
    """Test getting block details using block hash"""
    known_hash = "0x" + "deadbeef" * 8
    response = client.get(f"/v1/explorer/block/{known_hash}")
    assert response.status_code == 200

    data = response.json()
    assert data["number"] == 2000
    assert data["transaction_count"] == 10
    assert data["internal_transaction_count"] == 5


def test_get_latest_block(client, session, sample_blocks_details):
    """Test getting the latest block and verifying is_last_block flag"""
    response = client.get("/v1/explorer/block/2000")
    assert response.status_code == 200

    data = response.json()
    assert data["is_last_block"] == True


def test_get_block_not_found(client, session, sample_blocks_details):
    """Test response when block is not found"""
    # Test with non-existent block number
    response = client.get("/v1/explorer/block/9999")
    assert response.status_code == 404

    # Test with non-existent block hash
    response = client.get("/v1/explorer/block/0x" + "a" * 64)
    assert response.status_code == 404


def test_get_block_invalid_input(client, session, sample_blocks_details):
    """Test response with invalid input formats"""
    # Invalid hash length
    response = client.get("/v1/explorer/block/0x123")
    assert response.status_code == 400

    # Invalid hex string
    response = client.get("/v1/explorer/block/0x" + "g" * 64)
    assert response.status_code == 400

    # Invalid format
    response = client.get("/v1/explorer/block/not-a-block")
    assert response.status_code == 400


def test_get_block_with_zero_counts(client, session, sample_blocks_details):
    """Test block with zero transaction counts"""
    response = client.get("/v1/explorer/block/1000")
    assert response.status_code == 200

    data = response.json()
    assert data["transaction_count"] == 0
    assert data["internal_transaction_count"] == 0


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
