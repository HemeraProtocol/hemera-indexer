#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/22 18:01
# @Author  ideal93
# @File  transaction_test.py.py
# @Brief

import pytest

from hemera.app.api.routes.helper.transaction import *
from hemera.app.api.routes.helper.transaction import _get_transaction_by_hash
from hemera.common.models.transactions import Transactions
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture
def sample_transactions(session):
    now = datetime.utcnow()
    transactions = [
        Transactions(
            hash=hex_str_to_bytes("0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            block_number=21436149,
            block_timestamp=now,
            from_address=hex_str_to_bytes("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),
            to_address=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
            transaction_index=0,
        ),
        Transactions(
            hash=hex_str_to_bytes("0x2234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            block_number=21436149,
            block_timestamp=now,
            from_address=hex_str_to_bytes("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),
            to_address=hex_str_to_bytes("0xcccccccccccccccccccccccccccccccccccccccc"),
            transaction_index=1,
        ),
        Transactions(
            hash=hex_str_to_bytes("0x3234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            block_number=21436148,
            block_timestamp=now - timedelta(minutes=2),
            from_address=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
            to_address=hex_str_to_bytes("0xcccccccccccccccccccccccccccccccccccccccc"),
            transaction_index=0,
        ),
    ]

    for tx in transactions:
        session.add(tx)
    session.commit()

    return transactions


@pytest.fixture
def sample_daily_stats(session):
    now = datetime.utcnow()
    stats = DailyTransactionsStats(block_date=now.date(), total_cnt=1000, success_cnt=950, failed_cnt=50)
    session.add(stats)
    session.commit()
    return stats


def test_get_last_transaction(session, sample_transactions):
    tx = get_last_transaction(session)
    assert tx is not None
    assert tx.block_number == 21436149
    assert tx.transaction_index == 1
    assert tx.hash == hex_str_to_bytes("0x2234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")

    # Test with specific columns
    tx = get_last_transaction(session, columns=["hash", "block_number"])
    assert tx.hash == hex_str_to_bytes("0x2234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
    assert tx.block_number == 21436149
    with pytest.raises(AttributeError):
        _ = tx.block_timestamp


def test_get_transaction_by_hash(session, sample_transactions):
    tx = _get_transaction_by_hash(session, "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
    assert tx is not None
    assert tx.block_number == 21436149
    assert tx.transaction_index == 0

    # Test non-existent hash
    tx = _get_transaction_by_hash(session, "0xffff")
    assert tx is None

    # Test invalid hash
    with pytest.raises(ValueError):
        _get_transaction_by_hash(session, "invalid_hash")

    # Test with specific columns
    tx_block_number = _get_transaction_by_hash(
        session, "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef", columns="block_number"
    )
    assert tx_block_number == 21436149


def test_get_transactions_by_address(session, sample_transactions):
    # Test "from" direction
    txs = get_transactions_by_address(session, "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", direction="from")
    assert len(txs) == 2
    assert all(tx.from_address == "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" for tx in txs)

    # Test "to" direction
    txs = get_transactions_by_address(session, "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", direction="to")
    assert len(txs) == 1
    assert txs[0].to_address == "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

    # Test "both" direction
    txs = get_transactions_by_address(session, "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", direction="both")
    assert len(txs) == 2

    # Test with limit and offset
    txs = get_transactions_by_address(session, "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", limit=1, offset=1)
    assert len(txs) == 1
    assert txs[0].hash == "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

    # Test with specific columns
    txs = get_transactions_by_address(
        session,
        "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    )


def test_get_tps_latest_10min(session, sample_transactions):
    now = datetime.utcnow()
    tps = get_tps_latest_10min(session, now)
    assert tps == pytest.approx(0.005, rel=1e-2)  # 3 transactions in 600 seconds


def test_get_total_transaction_count(session, sample_transactions, sample_daily_stats):
    count = get_total_transaction_count(session)
    assert count > 1000  # Should be daily stats total + recent transactions


def test_get_transactions_by_condition(session, sample_transactions):
    # Test without condition
    txs = get_transactions_by_condition(session)
    assert len(txs) == 3
    assert txs[0].block_number == 21436149
    assert txs[0].transaction_index == 1

    # Test with condition
    txs = get_transactions_by_condition(session, filter_condition=(Transactions.block_number == 21436149))
    assert len(txs) == 2
    assert all(tx.block_number == 21436149 for tx in txs)

    # Test with limit
    txs = get_transactions_by_condition(session, limit=2)
    assert len(txs) == 2

    # Test with offset
    txs = get_transactions_by_condition(session, offset=1, limit=1)
    assert len(txs) == 1
    assert txs[0].hash == hex_str_to_bytes("0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")

    # Test with specific columns
    txs = get_transactions_by_condition(session, columns="block_number")
    assert len(txs) == 3
    with pytest.raises(AttributeError):
        _ = txs[0].hash


def test_get_transactions_count_by_condition(session, sample_transactions):
    # Test without condition
    count = get_transactions_count_by_condition(session)
    assert count == 3

    # Test with condition
    count = get_transactions_count_by_condition(session, filter_condition=(Transactions.block_number == 21436149))
    assert count == 2


def test_transaction_isolation(session, sample_transactions):
    with session.begin():
        new_tx = Transactions(
            hash=hex_str_to_bytes("0x9934567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            block_number=21436150,
            block_timestamp=datetime.utcnow(),
            from_address=hex_str_to_bytes("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),
            to_address=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
            transaction_index=0,
        )
        session.add(new_tx)

        last_tx = get_last_transaction(session)
        assert last_tx.block_number == 21436150

        session.rollback()

    last_tx = get_last_transaction(session)
    assert last_tx.block_number == 21436149


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
