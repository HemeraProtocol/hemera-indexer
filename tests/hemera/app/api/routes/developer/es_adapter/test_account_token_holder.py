#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/4 14:09
# @Author  ideal93
# @File  test_account_token_holder.py
# @Brief

from datetime import datetime

import pytest
from sqlalchemy import delete
from sqlmodel import Session

from hemera.app.api.routes.developer.es_adapter.helper import account_address_token_holding
from hemera.common.enumeration.token_type import TokenType
from hemera.common.models.current_token_balances import CurrentTokenBalances
from hemera.common.models.tokens import Tokens
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture(autouse=True)
def clean_db(session: Session):
    session.exec(delete(Tokens))
    session.exec(delete(CurrentTokenBalances))
    session.commit()


@pytest.fixture
def sample_token_data(session: Session):
    """Create sample token data for testing."""
    base_time = datetime(2025, 1, 1, 12, 0, 0)

    # Create token records (ERC20, ERC721, ERC1155)
    tokens = [
        Tokens(
            address=hex_str_to_bytes("0x" + "A" * 40),
            name="Sample ERC20",
            symbol="SERC20",
            decimals=18,
            token_type="ERC20",
        ),
        Tokens(
            address=hex_str_to_bytes("0x" + "B" * 40),
            name="Sample ERC721",
            symbol="SERC721",
            decimals=0,
            token_type="ERC721",
        ),
        Tokens(
            address=hex_str_to_bytes("0x" + "C" * 40),
            name="Sample ERC1155",
            symbol="SERC1155",
            decimals=0,
            token_type="ERC1155",
        ),
    ]
    session.add_all(tokens)
    session.commit()

    # Create current token balances
    balances = [
        CurrentTokenBalances(
            address=hex_str_to_bytes("0x" + "1" * 40),
            token_address=hex_str_to_bytes("0x" + "A" * 40),
            balance=1000,
            token_type="ERC20",
            token_id=-1,
            block_number=1000,
        ),
        CurrentTokenBalances(
            address=hex_str_to_bytes("0x" + "1" * 40),
            token_address=hex_str_to_bytes("0x" + "B" * 40),
            balance=5,
            token_type="ERC721",
            token_id=-1,
            block_number=1000,
        ),
        CurrentTokenBalances(
            address=hex_str_to_bytes("0x" + "1" * 40),
            token_address=hex_str_to_bytes("0x" + "C" * 40),
            balance=10,
            token_type="ERC1155",
            token_id=2,
            block_number=1000,
        ),
        CurrentTokenBalances(
            address=hex_str_to_bytes("0x" + "2" * 40),
            token_address=hex_str_to_bytes("0x" + "A" * 40),
            balance=500,
            token_type="ERC20",
            token_id=-1,
            block_number=1000,
        ),
    ]
    session.add_all(balances)
    session.commit()

    return {
        "erc20_contract": "0x" + "a" * 40,
        "erc721_contract": "0x" + "b" * 40,
        "erc1155_contract": "0x" + "c" * 40,
        "address_1": "0x" + "1" * 40,
        "address_2": "0x" + "2" * 40,
    }


def test_account_address_token_holding_erc20(session: Session, sample_token_data):
    """Test fetching ERC20 token holdings for an address."""
    result = account_address_token_holding(
        session=session, address=sample_token_data["address_1"], page=1, offset=10, token_type=TokenType.ERC20
    )

    assert len(result) == 1
    assert result[0].TokenAddress == sample_token_data["erc20_contract"].lower()
    assert result[0].TokenName == "Sample ERC20"
    assert result[0].TokenSymbol == "SERC20"
    assert result[0].TokenQuantity == "1000"
    assert result[0].TokenType == "ERC20"
    assert result[0].TokenDecimals == "18"
    assert result[0].TokenID is None


def test_account_address_token_holding_erc721(session: Session, sample_token_data):
    """Test fetching ERC721 token holdings for an address."""
    result = account_address_token_holding(
        session=session, address=sample_token_data["address_1"], page=1, offset=10, token_type=TokenType.ERC721
    )

    assert len(result) == 1
    assert result[0].TokenAddress == sample_token_data["erc721_contract"]
    assert result[0].TokenName == "Sample ERC721"
    assert result[0].TokenSymbol == "SERC721"
    assert result[0].TokenQuantity == "5"
    assert result[0].TokenType == "ERC721"
    assert result[0].TokenDecimals is None
    assert result[0].TokenID == None


def test_account_address_token_holding_erc1155(session: Session, sample_token_data):
    """Test fetching ERC1155 token holdings for an address."""
    result = account_address_token_holding(
        session=session, address=sample_token_data["address_1"], page=1, offset=10, token_type=TokenType.ERC1155
    )

    assert len(result) == 1
    assert result[0].TokenAddress == sample_token_data["erc1155_contract"]
    assert result[0].TokenName == "Sample ERC1155"
    assert result[0].TokenSymbol == "SERC1155"
    assert result[0].TokenQuantity == "10"
    assert result[0].TokenType == "ERC1155"
    assert result[0].TokenDecimals is None
    assert result[0].TokenID == "2"


def test_account_address_token_holding_multiple_tokens(session: Session, sample_token_data):
    """Test fetching multiple token types for an address."""
    result = account_address_token_holding(
        session=session, address=sample_token_data["address_1"], page=1, offset=10, token_type=TokenType.ERC20
    )
    assert len(result) == 1  # Only one ERC20 token for address_1
    assert result[0].TokenAddress == sample_token_data["erc20_contract"]

    result = account_address_token_holding(
        session=session, address=sample_token_data["address_1"], page=1, offset=10, token_type=TokenType.ERC721
    )
    assert len(result) == 1  # Only one ERC721 token for address_1
    assert result[0].TokenAddress == sample_token_data["erc721_contract"]

    result = account_address_token_holding(
        session=session, address=sample_token_data["address_1"], page=1, offset=10, token_type=TokenType.ERC1155
    )
    assert len(result) == 1  # Only one ERC1155 token for address_1
    assert result[0].TokenAddress == sample_token_data["erc1155_contract"]


def test_account_address_token_holding_pagination(session: Session, sample_token_data):
    """Test pagination when fetching token holdings for an address."""
    result_page1 = account_address_token_holding(
        session=session, address=sample_token_data["address_1"], page=1, offset=2, token_type=TokenType.ERC20
    )
    result_page2 = account_address_token_holding(
        session=session, address=sample_token_data["address_1"], page=2, offset=2, token_type=TokenType.ERC20
    )

    assert len(result_page1) == 1  # ERC20 token, so 1


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
