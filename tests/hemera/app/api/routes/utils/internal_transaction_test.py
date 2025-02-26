#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/26 15:14
# @Author  ideal93
# @File  internal_transaction_test.py
# @Brief

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlmodel import Session, asc, desc

from hemera.app.api.routes.helper.internal_transaction import (
    _get_internal_transactions_by_address_native,
    get_internal_transactions_by_address,
    get_internal_transactions_by_address_using_address_index,
    get_internal_transactions_count_by_address,
    get_internal_transactions_count_by_address_native,
    get_internal_transactions_count_by_address_using_address_index,
)
from hemera.common.enumeration.txn_type import InternalTransactionType
from hemera.common.models.address.address_internal_transaciton import AddressInternalTransactions
from hemera.common.models.traces import ContractInternalTransactions
from hemera.common.utils.format_utils import hex_str_to_bytes

# Test data constants
TEST_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e".lower()
TEST_ADDRESS_2 = "0x742d35Cc6634C0532925a3b844Bc454e4438f44f".lower()
TEST_TRANSACTION_HASH = "0x123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234".lower()
TEST_BLOCK_HASH = "0xabcdef123456789abcdef123456789abcdef123456789abcdef123456789abc1".lower()


@pytest.fixture(name="sample_contract_txns")
def sample_contract_txns_fixture(session: Session):
    """Create sample internal transactions in the database"""
    transactions = []
    # Create multiple transactions with different properties
    for i in range(5):
        tx = ContractInternalTransactions(
            trace_id=f"trace_{i}",
            from_address=hex_str_to_bytes(TEST_ADDRESS if i % 2 == 0 else TEST_ADDRESS_2),
            to_address=hex_str_to_bytes(TEST_ADDRESS_2 if i % 2 == 0 else TEST_ADDRESS),
            value=Decimal(str(i + 1)) * Decimal("1000000000000000000"),
            gas=Decimal("21000"),
            gas_used=Decimal("21000"),
            trace_type="call",
            call_type="call",
            status=1,
            block_number=1000 + i,
            block_hash=hex_str_to_bytes(TEST_BLOCK_HASH),
            block_timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            transaction_hash=hex_str_to_bytes(TEST_TRANSACTION_HASH),
            transaction_index=0,
        )
        transactions.append(tx)
        session.add(tx)

    session.commit()
    return transactions


@pytest.fixture(name="sample_address_txns")
def sample_address_txns_fixture(session: Session):
    """Create sample address internal transactions in the database"""
    transactions = []
    # Create multiple transactions with different types
    for i in range(5):
        tx = AddressInternalTransactions(
            trace_id=f"trace_{i}",
            address=hex_str_to_bytes(TEST_ADDRESS),
            related_address=hex_str_to_bytes(TEST_ADDRESS_2),
            value=Decimal(str(i + 1)) * Decimal("1000000000000000000"),
            gas=Decimal("21000"),
            gas_used=Decimal("21000"),
            trace_type="call",
            call_type="call",
            txn_type=InternalTransactionType.SENDER.value if i % 2 == 0 else InternalTransactionType.RECEIVER.value,
            status=1,
            block_number=1000 + i,
            block_hash=hex_str_to_bytes(TEST_BLOCK_HASH),
            block_timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            transaction_hash=hex_str_to_bytes(TEST_TRANSACTION_HASH),
            transaction_index=i,
        )
        transactions.append(tx)
        session.add(tx)

    session.commit()
    return transactions


def test_get_internal_transactions_both_directions(session: Session, sample_contract_txns):
    """Test getting transactions for both directions without using index"""
    result = get_internal_transactions_by_address(session=session, address=TEST_ADDRESS, direction="both", limit=10)

    assert len(result) == 5
    # Verify first transaction details
    tx = result[0]
    assert tx.trace_id == "trace_4"
    assert tx.value == Decimal("5000000000000000000")
    assert tx.from_address == TEST_ADDRESS
    assert tx.to_address == TEST_ADDRESS_2


def test_get_internal_transactions_from_direction(session: Session, sample_contract_txns):
    """Test getting only 'from' transactions without using index"""
    result = get_internal_transactions_by_address(session=session, address=TEST_ADDRESS, direction="from", limit=10)

    assert len(result) == 3
    for tx in result:
        assert tx.from_address == TEST_ADDRESS


def test_get_internal_transactions_to_direction(session: Session, sample_contract_txns):
    """Test getting only 'to' transactions without using index"""
    result = get_internal_transactions_by_address(session=session, address=TEST_ADDRESS, direction="to", limit=10)

    assert len(result) == 2
    for tx in result:
        assert tx.to_address == TEST_ADDRESS


def test_get_internal_transactions_with_limit_offset(session: Session, sample_contract_txns):
    """Test pagination functionality"""
    result = get_internal_transactions_by_address(session=session, address=TEST_ADDRESS, limit=2, offset=1)

    assert len(result) == 2


def test_get_internal_transactions_using_index_both_directions(session: Session, sample_address_txns):
    """Test getting transactions using address index for both directions"""
    result = get_internal_transactions_by_address(
        session=session, address=TEST_ADDRESS, direction="both", limit=10, use_address_index=True
    )

    assert len(result) == 5
    # Verify conversion of sender/receiver types
    first_tx = result[0]
    assert first_tx.trace_id == "trace_4"
    assert first_tx.from_address == TEST_ADDRESS
    assert first_tx.to_address == TEST_ADDRESS_2


def test_get_internal_transactions_using_index_from_direction(session: Session, sample_address_txns):
    """Test getting only 'from' transactions using address index"""
    result = get_internal_transactions_by_address(
        session=session, address=TEST_ADDRESS, direction="from", limit=10, use_address_index=True
    )

    assert len(result) == 3  # Includes SENDER and SELF_CALL types
    for tx in result:
        assert tx.from_address == TEST_ADDRESS


def test_get_internal_transactions_using_index_to_direction(session: Session, sample_address_txns):
    """Test getting only 'to' transactions using address index"""
    result = get_internal_transactions_by_address(
        session=session, address=TEST_ADDRESS, direction="to", limit=10, use_address_index=True
    )

    assert len(result) == 2  # Includes RECEIVER types
    for tx in result:
        assert tx.to_address == TEST_ADDRESS


def test_get_internal_transactions_specific_columns(session: Session, sample_contract_txns):
    """Test retrieving specific columns only"""
    result = get_internal_transactions_by_address(
        session=session,
        address=TEST_ADDRESS,
    )

    assert len(result) == 5
    tx = result[0]
    assert tx.block_number is not None
    assert tx.transaction_hash is not None
    assert tx.value is not None


def test_invalid_address_format(session: Session):
    """Test error handling for invalid address format"""
    with pytest.raises(ValueError):
        get_internal_transactions_by_address(session=session, address="invalid_address")


# Tests for get_internal_transactions_by_address
def test_get_internal_transactions_by_address_both(session: Session, sample_contract_txns):
    """Test getting transactions from both directions using contract table"""
    result = _get_internal_transactions_by_address_native(session=session, address=TEST_ADDRESS, direction="both")

    assert len(result) == 5
    # Check if transactions are ordered by block number desc
    assert all(result[i].block_number >= result[i + 1].block_number for i in range(len(result) - 1))

    # Verify some are from and some are to transactions
    from_count = sum(1 for tx in result if tx.from_address == hex_str_to_bytes(TEST_ADDRESS))
    to_count = sum(1 for tx in result if tx.to_address == hex_str_to_bytes(TEST_ADDRESS))
    assert from_count > 0 and to_count > 0
    assert from_count + to_count == 5


def test_get_internal_transactions_by_address_from(session: Session, sample_contract_txns):
    """Test getting only from transactions using contract table"""
    result = _get_internal_transactions_by_address_native(session=session, address=TEST_ADDRESS, direction="from")

    assert len(result) == 3
    assert all(tx.from_address == hex_str_to_bytes(TEST_ADDRESS) for tx in result)


def test_get_internal_transactions_by_address_to(session: Session, sample_contract_txns):
    """Test getting only to transactions using contract table"""
    result = _get_internal_transactions_by_address_native(session=session, address=TEST_ADDRESS, direction="to")

    assert len(result) == 2
    assert all(tx.to_address == hex_str_to_bytes(TEST_ADDRESS) for tx in result)


def test_get_internal_transactions_by_address_columns(session: Session, sample_contract_txns):
    """Test getting specific columns from contract table"""
    result = _get_internal_transactions_by_address_native(
        session=session, address=TEST_ADDRESS, columns=["block_number", "transaction_hash"]
    )

    assert len(result) == 5
    # Verify only requested columns are available
    tx = result[0]
    assert hasattr(tx, "block_number")
    assert hasattr(tx, "transaction_hash")
    with pytest.raises(AttributeError):
        _ = tx.value


def test_get_internal_transactions_by_address_pagination(session: Session, sample_contract_txns):
    """Test pagination in contract table query"""
    result = _get_internal_transactions_by_address_native(session=session, address=TEST_ADDRESS, limit=2, offset=1)

    assert len(result) == 2
    assert result[0].block_number == 1003  # Based on test data setup


# Tests for get_internal_transactions_by_address_using_address_index
def test_get_internal_transactions_by_address_using_index_both(session: Session, sample_address_txns):
    """Test getting transactions from both directions using address index"""
    result = get_internal_transactions_by_address_using_address_index(
        session=session, address=TEST_ADDRESS, direction="both"
    )

    assert len(result) == 5
    assert all(tx.address == hex_str_to_bytes(TEST_ADDRESS) for tx in result)
    # Check ordering
    assert all(result[i].block_number >= result[i + 1].block_number for i in range(len(result) - 1))


def test_get_internal_transactions_by_address_using_index_from(session: Session, sample_address_txns):
    """Test getting only from transactions using address index"""
    result = get_internal_transactions_by_address_using_address_index(
        session=session, address=TEST_ADDRESS, direction="from"
    )

    assert len(result) == 3  # Including SENDER and SELF_CALL types
    assert all(
        tx.txn_type in [InternalTransactionType.SENDER.value, InternalTransactionType.SELF_CALL.value] for tx in result
    )


def test_get_internal_transactions_by_address_using_index_to(session: Session, sample_address_txns):
    """Test getting only to transactions using address index"""
    result = get_internal_transactions_by_address_using_address_index(
        session=session, address=TEST_ADDRESS, direction="to"
    )

    assert len(result) == 2  # Including RECEIVER type
    assert all(
        tx.txn_type in [InternalTransactionType.RECEIVER.value, InternalTransactionType.SELF_CALL.value]
        for tx in result
    )


def test_get_internal_transactions_by_address_using_index_columns(session: Session, sample_address_txns):
    """Test getting specific columns using address index"""
    result = get_internal_transactions_by_address_using_address_index(
        session=session, address=TEST_ADDRESS, columns=["block_number", "transaction_hash", "txn_type"]
    )

    assert len(result) == 5
    # Verify only requested columns are available
    tx = result[0]
    assert hasattr(tx, "block_number")
    assert hasattr(tx, "transaction_hash")
    assert hasattr(tx, "txn_type")
    with pytest.raises(AttributeError):
        _ = tx.value


def test_get_internal_transactions_by_address_using_index_pagination(session: Session, sample_address_txns):
    """Test pagination in address index query"""
    result = get_internal_transactions_by_address_using_address_index(
        session=session, address=TEST_ADDRESS, limit=2, offset=1
    )

    assert len(result) == 2
    assert result[0].block_number == 1003  # Based on test data setup


# Tests for internal transaction count functions
def test_get_internal_transactions_count_without_index(session: Session, sample_contract_txns):
    """Test getting internal transaction count without using index"""
    # Test both directions
    count = get_internal_transactions_count_by_address(
        session=session, address=TEST_ADDRESS, direction="both", use_address_index=False
    )
    assert count == 5

    # Test from direction
    count = get_internal_transactions_count_by_address(
        session=session, address=TEST_ADDRESS, direction="from", use_address_index=False
    )
    assert count == 3

    # Test to direction
    count = get_internal_transactions_count_by_address(
        session=session, address=TEST_ADDRESS, direction="to", use_address_index=False
    )
    assert count == 2


def test_get_internal_transactions_count_with_index(session: Session, sample_address_txns):
    """Test getting internal transaction count using address index"""
    # Test both directions
    count = get_internal_transactions_count_by_address(
        session=session, address=TEST_ADDRESS, direction="both", use_address_index=True
    )
    assert count == 5

    # Test from direction (SENDER transactions)
    count = get_internal_transactions_count_by_address(
        session=session, address=TEST_ADDRESS, direction="from", use_address_index=True
    )
    assert count == 3  # SENDER transactions (i % 2 == 0)

    # Test to direction (RECEIVER transactions)
    count = get_internal_transactions_count_by_address(
        session=session, address=TEST_ADDRESS, direction="to", use_address_index=True
    )
    assert count == 2  # RECEIVER transactions (i % 2 != 0)


def test_get_internal_transactions_count_empty_db(session: Session, clean_db):
    """Test count functions with empty database"""
    # Test without index
    count = get_internal_transactions_count_by_address(
        session=session,
        address=TEST_ADDRESS,
    )
    assert count == 0

    # Test with index
    count = get_internal_transactions_count_by_address(session=session, address=TEST_ADDRESS, use_address_index=True)
    assert count == 0


def test_get_internal_transactions_by_address_count_direction_filters(session: Session, sample_contract_txns):
    """Test direct count function with different direction filters"""
    # Test default (both) direction
    count = get_internal_transactions_count_by_address_native(session=session, address=TEST_ADDRESS)
    assert count == 5

    # Test from direction
    count = get_internal_transactions_count_by_address_native(session=session, address=TEST_ADDRESS, direction="from")
    assert count == 3

    # Test to direction
    count = get_internal_transactions_count_by_address_native(session=session, address=TEST_ADDRESS, direction="to")
    assert count == 2


def test_get_internal_transactions_by_address_using_index_count_types(session: Session, sample_address_txns):
    """Test count function using index with different transaction types"""
    # Test from direction (SENDER type)
    count = get_internal_transactions_count_by_address_using_address_index(
        session=session, address=TEST_ADDRESS, direction="from"
    )
    # Should count SENDER transactions (where i % 2 == 0)
    assert count == 3

    # Test to direction (RECEIVER type)
    count = get_internal_transactions_count_by_address_using_address_index(
        session=session, address=TEST_ADDRESS, direction="to"
    )
    # Should count RECEIVER transactions (where i % 2 != 0)
    assert count == 2


def test_get_internal_transactions_count_invalid_address(session: Session):
    """Test count functions with invalid address format"""
    # Test main count function
    with pytest.raises(ValueError):
        get_internal_transactions_count_by_address(session=session, address="invalid_address")

    # Test without index count function
    with pytest.raises(ValueError):
        get_internal_transactions_count_by_address_native(session=session, address="invalid_address")

    # Test with index count function
    with pytest.raises(ValueError):
        get_internal_transactions_count_by_address_using_address_index(session=session, address="invalid_address")


def test_get_internal_transactions_count_non_existent_address(session: Session, sample_contract_txns):
    """Test count functions with valid but non-existent address"""
    non_existent_address = "0x" + "1" * 40

    # Test without index
    count = get_internal_transactions_count_by_address(session=session, address=non_existent_address)
    assert count == 0

    # Test with index
    count = get_internal_transactions_count_by_address(
        session=session, address=non_existent_address, use_address_index=True
    )
    assert count == 0


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
