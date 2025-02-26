#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/3 03:50
# @Author  ideal93
# @File  test_contract.py.py
# @Brief

from datetime import datetime

import pytest
from sqlmodel import Session, delete, select

from hemera.app.api.routes.developer.es_adapter.helper import (
    check_contract_execution_status,
    check_transaction_receipt_status,
)
from hemera.common.models.traces import Traces
from hemera.common.models.transactions import Transactions
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture(autouse=True)
def clean_db(session: Session):
    """
    Clean the database before each test by deleting rows from the Traces and Transactions tables.
    """
    session.exec(delete(Traces))
    session.exec(delete(Transactions))
    session.commit()


@pytest.fixture
def sample_trace_success(session: Session):
    """
    Create a sample trace with a successful execution.
    In this case, status is non-zero indicating success, so isError should be "0".
    """
    # Use a sample transaction hash.
    txn_hash = "0x" + "1" * 64
    trace_record = Traces(
        transaction_hash=hex_str_to_bytes(txn_hash),
        trace_address=[],  # matching the query filter
        status=1,  # success status (non-zero)
        error="",  # no error message
        trace_id="1",
    )
    session.add(trace_record)
    session.commit()
    return txn_hash


@pytest.fixture
def sample_trace_failure(session: Session):
    """
    Create a sample trace with a failure execution.
    Here, status is 0, so isError should be "1" and errDescription should contain the error message.
    """
    txn_hash = "0x" + "2" * 64
    trace_record = Traces(
        transaction_hash=hex_str_to_bytes(txn_hash),
        trace_address=[],
        status=0,  # indicates failure
        error="Contract reverted due to insufficient gas",
        trace_id="2",
    )
    session.add(trace_record)
    session.commit()
    return txn_hash


@pytest.fixture
def sample_transaction(session: Session):
    """
    Create a sample transaction with a receipt_status.
    """
    txn_hash = "0x" + "3" * 64
    tx = Transactions(
        hash=hex_str_to_bytes(txn_hash),
        block_number=1500,
        block_timestamp=datetime.utcnow(),
        nonce=1,
        block_hash=hex_str_to_bytes("0x" + "a" * 64),
        input=None,
        transaction_index=1,
        from_address=hex_str_to_bytes("0x" + "b" * 40),
        to_address=hex_str_to_bytes("0x" + "c" * 40),
        value=500000,
        gas=21000,
        gas_price=10000000000,
        receipt_status=1,  # A sample receipt status (could be 0 or 1)
        receipt_contract_address=None,
        receipt_cumulative_gas_used=21000,
        receipt_gas_used=21000,
    )
    session.add(tx)
    session.commit()
    return txn_hash


def test_check_contract_execution_status_success(session: Session, sample_trace_success):
    """
    Test that check_contract_execution_status returns a status indicating success.
    """
    result = check_contract_execution_status(session, sample_trace_success)
    # For a successful trace, status is non-zero so isError should be "0" and error message empty.
    assert result is not None
    assert result.isError == "0"
    assert result.errDescription == ""


def test_check_contract_execution_status_failure(session: Session, sample_trace_failure):
    """
    Test that check_contract_execution_status returns a status indicating failure with the proper error message.
    """
    result = check_contract_execution_status(session, sample_trace_failure)
    # For a failed trace, status is 0 so isError should be "1" and error message should match.
    assert result is not None
    assert result.isError == "1"
    assert result.errDescription == "Contract reverted due to insufficient gas"


def test_check_contract_execution_status_none(session: Session):
    """
    Test that check_contract_execution_status returns None if no trace record is found.
    """
    # Use a txn_hash that was not inserted into the Traces table.
    missing_txn_hash = "0x" + "f" * 64
    result = check_contract_execution_status(session, missing_txn_hash)
    assert result is None


def test_check_transaction_receipt_status_found(session: Session, sample_transaction):
    """
    Test that check_transaction_receipt_status returns the correct receipt status when the transaction exists.
    """
    result = check_transaction_receipt_status(session, sample_transaction)
    # The fixture sets receipt_status to 1.
    assert result is not None
    # The returned status is converted to string.
    assert result.status == "1"


def test_check_transaction_receipt_status_none(session: Session):
    """
    Test that check_transaction_receipt_status returns None when the transaction is not found.
    """
    missing_txn_hash = "0x" + "e" * 64
    result = check_transaction_receipt_status(session, missing_txn_hash)
    assert result is None


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
