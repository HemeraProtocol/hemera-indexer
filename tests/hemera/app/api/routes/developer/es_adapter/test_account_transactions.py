#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/2 15:41
# @Author  ideal93
# @File  test_account_transactions.py
# @Brief

from datetime import datetime, timedelta

import pytest
from sqlmodel import delete

from hemera.app.api.routes.developer.es_adapter.helper import account_txlist, account_txlistinternal
from hemera.common.models.traces import ContractInternalTransactions
from hemera.common.models.transactions import Transactions
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture(autouse=True)
def clean_db(session):
    """Clean database before each test"""
    session.exec(delete(ContractInternalTransactions))
    session.exec(delete(Transactions))
    session.commit()


@pytest.mark.serial
@pytest.fixture
def sample_transactions(clean_db, session):
    """Create a set of test transactions"""
    transactions = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    # Create 5 test transactions
    for i in range(5):
        tx = Transactions(
            hash=hex_str_to_bytes(f"0x{i:064x}"),
            block_number=1000 + i,
            block_timestamp=base_time + timedelta(minutes=i),
            nonce=i,
            block_hash=hex_str_to_bytes(f"0x{i:064x}"),
            input=None,
            transaction_index=i,
            from_address=hex_str_to_bytes(f"0x{1:040x}"),
            to_address=hex_str_to_bytes(f"0x{2:040x}"),
            value=1000000 * (i + 1),
            gas=21000,
            gas_price=20000000000,
            receipt_status=1,
            receipt_contract_address=None,
            receipt_cumulative_gas_used=21000 * (i + 1),
            receipt_gas_used=21000,
        )
        transactions.append(tx)
        session.add(tx)

    session.commit()
    return transactions


@pytest.mark.serial
@pytest.fixture
def sample_internal_transactions(clean_db, session):
    """Create a set of test internal transactions"""
    internal_txs = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    # Create 5 test internal transactions
    for i in range(5):
        tx = ContractInternalTransactions(
            transaction_hash=hex_str_to_bytes(f"0x{i:064x}"),
            block_number=1000 + i,
            block_timestamp=base_time + timedelta(minutes=i),
            from_address=hex_str_to_bytes(f"0x{1:040x}"),
            to_address=hex_str_to_bytes(f"0x{2:040x}"),
            value=1000000 * (i + 1),
            trace_type="call",
            gas=21000,
            gas_used=21000,
            trace_id=str(i),
            error=0,
        )
        internal_txs.append(tx)
        session.add(tx)

    session.commit()
    return internal_txs


@pytest.mark.serial
@pytest.mark.es_api
def test_account_txlist(client, sample_transactions, session):
    """Test fetching normal transactions"""
    # Test by address
    txs = account_txlist(
        session,
        txhash=None,
        address=f"0x{1:040x}",  # from_address in sample data
        start_block=1000,
        end_block=1004,
        page=1,
        offset=10,
        sort_order="desc",
    )

    assert len(txs) == 5
    assert txs[0].blockNumber == "1004"
    assert txs[0].value == "5000000"

    # Test by transaction hash
    tx = account_txlist(
        session,
        txhash=f"0x{0:064x}",
        address=None,
        start_block=1000,
        end_block=1004,
        page=1,
        offset=10,
        sort_order="asc",
    )

    assert len(tx) == 1
    assert tx[0].blockNumber == "1000"
    assert tx[0].value == "1000000"


@pytest.mark.serial
@pytest.mark.es_api
def test_account_txlistinternal(client, sample_internal_transactions, session):
    """Test fetching internal transactions"""
    # Test by address
    txs = account_txlistinternal(
        session,
        txhash=None,
        address=f"0x{1:040x}",  # from_address in sample data
        start_block=1000,
        end_block=1004,
        page=1,
        offset=10,
        sort_order="desc",
    )

    assert len(txs) == 5
    assert txs[0].blockNumber == "1004"
    assert txs[0].value == "5000000"

    # Test by transaction hash
    tx = account_txlistinternal(
        session,
        txhash=f"0x{0:064x}",
        address=None,
        start_block=1000,
        end_block=1004,
        page=1,
        offset=10,
        sort_order="asc",
    )

    assert len(tx) == 1
    assert tx[0].blockNumber == "1000"
    assert tx[0].value == "1000000"

    tx = account_txlistinternal(
        session,
        txhash=f"0x{0:064x}",
        address=None,
        start_block=1000,
        end_block=1004,
        page=1,
        offset=10,
        sort_order="desc",
    )
    assert len(tx) == 1
    assert tx[0].blockNumber == "1000"
    assert tx[0].value == "1000000"
    assert tx[0].fromAddress == f"0x{1:040x}"
    assert tx[0].toAddress == f"0x{2:040x}"


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
