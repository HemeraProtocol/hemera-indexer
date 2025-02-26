#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/5 00:33
# @Author  ideal93
# @File  test_stats.py
# @Brief
from datetime import datetime

import pytest
from sqlmodel import Session, delete

from hemera.app.api.routes.developer.es_adapter.helper import (
    stats_daily_average_block_size,
    stats_daily_average_block_time,
    stats_daily_block_count_and_rewards,
    stats_daily_network_transaction_fee,
    stats_daily_network_utilization,
    stats_daily_new_address_count,
    stats_daily_transaction_count,
)
from hemera.common.models.stats.daily_addresses_stats import DailyAddressesStats
from hemera.common.models.stats.daily_blocks_stats import DailyBlocksStats
from hemera.common.models.stats.daily_transactions_stats import DailyTransactionsStats


@pytest.fixture(autouse=True)
def clean_db(session: Session):
    session.exec(delete(DailyTransactionsStats))
    session.exec(delete(DailyAddressesStats))
    session.exec(delete(DailyBlocksStats))
    session.commit()


@pytest.fixture
def sample_data(session: Session):
    """Create sample data for testing."""
    # Create DailyTransactionsStats sample data
    transactions = [
        DailyTransactionsStats(block_date=datetime(2025, 1, 1), avg_transaction_fee=1.23, cnt=1),
        DailyTransactionsStats(block_date=datetime(2025, 1, 2), avg_transaction_fee=2.34, cnt=1),
    ]
    session.add_all(transactions)

    # Create DailyAddressesStats sample data
    addresses = [
        DailyAddressesStats(block_date=datetime(2025, 1, 1), new_address_cnt=100),
        DailyAddressesStats(block_date=datetime(2025, 1, 2), new_address_cnt=150),
    ]
    session.add_all(addresses)

    # Create DailyBlocksStats sample data
    blocks = [
        DailyBlocksStats(
            block_date=datetime(2025, 1, 1), avg_size=1000, avg_gas_used_percentage=45.6, cnt=10, block_interval=12.5
        ),
        DailyBlocksStats(
            block_date=datetime(2025, 1, 2), avg_size=1200, avg_gas_used_percentage=50.7, cnt=12, block_interval=10.8
        ),
    ]
    session.add_all(blocks)

    session.commit()


# -----------------------------------------------------------------------------
# Test Cases for stats_daily_network_transaction_fee
# -----------------------------------------------------------------------------
def test_stats_daily_network_transaction_fee(session: Session, sample_data):
    result = stats_daily_network_transaction_fee(
        session=session,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 2),
        sort_order="asc",
    )

    assert len(result) == 2
    assert result[0].UTCDate == "2025-01-01"
    assert result[0].transactionFee == "1.23"
    assert result[1].UTCDate == "2025-01-02"
    assert result[1].transactionFee == "2.34"


# -----------------------------------------------------------------------------
# Test Cases for stats_daily_new_address_count
# -----------------------------------------------------------------------------
def test_stats_daily_new_address_count(session: Session, sample_data):
    result = stats_daily_new_address_count(
        session=session,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 2),
        sort_order="asc",
    )

    assert len(result) == 2
    assert result[0].newAddressCount == "100"
    assert result[1].newAddressCount == "150"


# -----------------------------------------------------------------------------
# Test Cases for stats_daily_network_utilization
# -----------------------------------------------------------------------------
def test_stats_daily_network_utilization(session: Session, sample_data):
    result = stats_daily_network_utilization(
        session=session,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 2),
        sort_order="asc",
    )

    assert len(result) == 2
    assert result[0].networkUtilization == "45.6"
    assert result[1].networkUtilization == "50.7"


# -----------------------------------------------------------------------------
# Test Cases for stats_daily_transaction_count
# -----------------------------------------------------------------------------
def test_stats_daily_transaction_count(session: Session, sample_data):
    result = stats_daily_transaction_count(
        session=session,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 2),
        sort_order="asc",
    )

    assert len(result) == 2
    assert result[0].transactionCount == "1"
    assert result[1].transactionCount == "1"


# -----------------------------------------------------------------------------
# Test Cases for stats_daily_average_block_size
# -----------------------------------------------------------------------------
def test_stats_daily_average_block_size(session: Session, sample_data):
    result = stats_daily_average_block_size(
        session=session,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 2),
        sort_order="asc",
    )

    assert len(result) == 2
    assert result[0].averageBlockSize == "1000"
    assert result[1].averageBlockSize == "1200"


# -----------------------------------------------------------------------------
# Test Cases for stats_daily_block_count_and_rewards
# -----------------------------------------------------------------------------
def test_stats_daily_block_count_and_rewards(session: Session, sample_data):
    result = stats_daily_block_count_and_rewards(
        session=session,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 2),
        sort_order="asc",
    )

    assert len(result) == 2
    assert result[0].blockCount == "10"
    assert result[1].blockCount == "12"


# -----------------------------------------------------------------------------
# Test Cases for stats_daily_average_block_time
# -----------------------------------------------------------------------------
def test_stats_daily_average_block_time(session: Session, sample_data):
    result = stats_daily_average_block_time(
        session=session,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 2),
        sort_order="asc",
    )

    assert len(result) == 2
    assert result[0].blockTime == "12.5"
    assert result[1].blockTime == "10.8"


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
