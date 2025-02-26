#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/20 14:02
# @Author  ideal93
# @File  token_test.py.py
# @Brief

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlmodel import delete

from hemera.app.api.routes.helper.token import get_coin_prices, get_latest_coin_price, get_token_price
from hemera.common.models.prices import CoinPrices, TokenHourlyPrices, TokenPrices


@pytest.fixture
def sample_token_prices(session):
    """Create sample token price data for testing

    Creates both current prices (TokenPrices) and historical hourly prices
    (TokenHourlyPrices) for multiple tokens.

    Args:
        session: SQLModel database session

    Returns:
        dict: Dictionary containing current and hourly price test data
    """
    # Create current token prices
    current_prices = [
        TokenPrices(symbol="ETH", price=Decimal("2000.50"), timestamp=datetime.utcnow()),
        TokenPrices(symbol="BTC", price=Decimal("45000.75"), timestamp=datetime.utcnow()),
        TokenPrices(symbol="USDT", price=Decimal("1.0"), timestamp=datetime.utcnow()),
    ]

    # Create historical hourly prices
    now = datetime.utcnow()
    hourly_prices = [
        TokenHourlyPrices(symbol="ETH", price=Decimal("1950.25"), timestamp=now - timedelta(hours=1)),
        TokenHourlyPrices(symbol="ETH", price=Decimal("1900.75"), timestamp=now - timedelta(hours=2)),
        TokenHourlyPrices(symbol="BTC", price=Decimal("44500.50"), timestamp=now - timedelta(hours=1)),
    ]

    # Add all prices to database
    for price in current_prices + hourly_prices:
        session.add(price)
    session.commit()

    return {"current": current_prices, "hourly": hourly_prices}


@pytest.fixture
def sample_coin_prices(session):
    """Create sample coin price data for testing

    Creates daily coin prices for the last 3 days.

    Args:
        session: SQLModel database session

    Returns:
        dict: Dictionary containing price data and corresponding dates
    """
    now = datetime.utcnow()
    dates = [datetime.combine(now.date() - timedelta(days=i), datetime.min.time()) for i in range(3)]

    coin_prices = [
        CoinPrices(symbol="TEST", price=Decimal("100.50"), block_date=dates[0]),
        CoinPrices(symbol="TEST", price=Decimal("98.75"), block_date=dates[1]),
        CoinPrices(symbol="TEST", price=Decimal("97.25"), block_date=dates[2]),
    ]

    for price in coin_prices:
        session.add(price)
    session.commit()

    return {"prices": coin_prices, "dates": dates}


def test_get_token_price_latest(session, sample_token_prices):
    """Test getting latest token prices

    Tests:
    1. Getting latest price for existing tokens
    2. Getting price for non-existent token
    """
    # Test getting latest price for existing tokens
    eth_price = get_token_price(session, "ETH")
    assert eth_price == Decimal("2000.50")

    btc_price = get_token_price(session, "BTC")
    assert btc_price == Decimal("45000.75")

    # Test getting price for non-existent token
    unknown_price = get_token_price(session, "UNKNOWN")
    assert unknown_price == Decimal("0.0")


def test_get_token_price_historical(session, sample_token_prices):
    """Test getting historical token prices

    Tests:
    1. Getting price at specific historical timestamps
    2. Getting price at non-existent historical timestamp
    """
    now = datetime.utcnow()

    # Test getting price from 1 hour ago
    eth_price = get_token_price(session, "ETH", date=now - timedelta(hours=1))
    assert eth_price == Decimal("1950.25")

    # Test getting price from 2 hours ago
    eth_price = get_token_price(session, "ETH", date=now - timedelta(hours=2))
    assert eth_price == Decimal("1900.75")

    # Test getting price from non-existent timestamp
    eth_price = get_token_price(session, "ETH", date=now - timedelta(days=7))
    assert eth_price == Decimal("0.0")


def test_get_coin_prices(session, sample_coin_prices):
    """Test getting coin prices for specific dates

    Tests:
    1. Getting prices for existing dates
    2. Getting prices for non-existent dates
    """
    # Test getting prices for existing dates
    dates = sample_coin_prices["dates"][:2]
    prices = get_coin_prices(session, dates)

    assert len(prices) == 2

    assert prices[1].block_date == dates[1]
    assert prices[1].price == Decimal("98.75")

    assert prices[0].block_date == dates[0]
    assert prices[0].price == Decimal("100.50")

    # Test getting prices for future date
    future_date = (datetime.utcnow() + timedelta(days=7)).date()
    empty_prices = get_coin_prices(session, [future_date])
    assert len(empty_prices) == 0


def test_get_latest_coin_price(session, sample_coin_prices):
    """Test getting latest coin price

    Tests:
    1. Getting latest price when prices exist
    2. Getting latest price when no prices exist
    """
    # Test getting latest price
    latest_price = get_latest_coin_price(session)
    assert latest_price == 100.50

    # Test getting latest price with empty database
    session.exec(delete(CoinPrices))
    session.commit()

    empty_price = get_latest_coin_price(session)
    assert empty_price == 0.0


def test_transaction_isolation_token_prices(session, sample_token_prices):
    """Test transaction isolation for token prices

    Tests that price changes within a transaction are properly isolated
    and can be rolled back.
    """
    # Test price changes within transaction
    with session.begin():
        new_price = TokenPrices(symbol="ETH", price=Decimal("2100.00"), timestamp=datetime.utcnow())
        session.add(new_price)

        # Price should be updated within transaction
        current_price = get_token_price(session, "ETH")
        assert current_price == Decimal("2100.00")

        session.rollback()

    # Price should be back to original after rollback
    final_price = get_token_price(session, "ETH")
    assert final_price == Decimal("2000.50")


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
