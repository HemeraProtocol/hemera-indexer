#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/2 14:59
# @Author  ideal93
# @File  test_account_balance.py
# @Brief
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from hemera.app.api.routes.developer.es_adapter.helper import (
    account_balance,
    account_balancehistory,
    account_balancemulti,
)
from hemera.app.main import app
from hemera.common.models.coin_balances import CoinBalances
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture(autouse=True)
def clean_db(session):
    """Clean database before each test"""
    # Order matters due to foreign key constraints
    session.exec(delete(CoinBalances))

    session.commit()


@pytest.mark.serial
@pytest.fixture
def client(engine):
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.serial
@pytest.fixture
def sample_coin_balance(clean_db, session):
    """Create a set of test blocks"""
    coin_balances = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    # Create 10 consecutive blocks
    for i in range(5):
        block = CoinBalances(
            address=hex_str_to_bytes(f"0x{i:040x}"),
            balance=1000000 * (i + 1),
            block_number=1000 + i,
            block_timestamp=base_time + timedelta(minutes=i),
        )
        coin_balances.append(block)
        session.add(block)

    session.commit()
    return coin_balances


@pytest.mark.serial
@pytest.mark.es_api
def test_account_balance(client, sample_coin_balance, session):
    """Test successful health check with single block"""

    balance = account_balance(session, f"0x{1:040x}")
    assert balance == 2000000

    balance = account_balance(session, f"0x{9:040x}")
    assert balance is None


@pytest.mark.serial
@pytest.mark.es_api
def test_account_balancemulti(client, sample_coin_balance, session):
    """Test fetching balance for multiple addresses"""
    addresses = [f"0x{0:040x}", f"0x{1:040x}", f"0x{3:040x}"]
    balances = account_balancemulti(session, addresses=addresses, tag=None)

    assert len(balances) == 3
    assert balances[0].balance == 1000000  # address 0
    assert balances[1].balance == 2000000  # address 1
    assert balances[2].balance == 4000000  # address 3


@pytest.mark.serial
@pytest.mark.es_api
def test_account_balancehistory(client, sample_coin_balance, session):
    """Test fetching historical balance at a specific block number"""
    balance = account_balancehistory(session, f"0x{2:040x}", 1002)
    assert balance == 3000000

    balance = account_balancehistory(session, f"0x{2:040x}", 999)
    assert balance == 0


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
