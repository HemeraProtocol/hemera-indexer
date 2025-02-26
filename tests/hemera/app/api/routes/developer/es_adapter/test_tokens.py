#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/3 21:43
# @Author  ideal93
# @File  test_tokens.py
# @Brief
from datetime import datetime

import pytest
from sqlmodel import Session, delete

from hemera.app.api.routes.developer.es_adapter.helper import (
    account_address_nft_inventory,
    account_token_balance,
    account_token_balance_with_block_number,
    stats_token_supply,
    token_holder_list,
    token_info,
)
from hemera.common.enumeration.token_type import TokenType
from hemera.common.models.current_token_balances import CurrentTokenBalances
from hemera.common.models.token_balances import AddressTokenBalances
from hemera.common.models.token_details import ERC721TokenIdDetails
from hemera.common.models.tokens import Tokens
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture(autouse=True)
def clean_db(session: Session):
    session.exec(delete(Tokens))
    session.exec(delete(AddressTokenBalances))
    session.exec(delete(CurrentTokenBalances))
    session.commit()


@pytest.fixture
def sample_token_data(session: Session):
    """Create sample token data for testing."""
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    # Create token records
    tokens = [
        Tokens(
            address=hex_str_to_bytes("0x" + "A" * 40),
            name="Sample ERC20",
            symbol="SERC20",
            total_supply=1000000,
            token_type="ERC20",
            decimals=18,
        ),
        Tokens(
            address=hex_str_to_bytes("0x" + "B" * 40),
            name="Sample ERC721",
            symbol="SERC721",
            total_supply=1000,
            token_type="ERC721",
            decimals=None,
            token_id=1,
        ),
        Tokens(
            address=hex_str_to_bytes("0x" + "C" * 40),
            name="Sample ERC1155",
            symbol="SERC1155",
            total_supply=5000,
            token_type="ERC1155",
            decimals=None,
            token_id=2,
        ),
    ]
    session.add_all(tokens)
    session.commit()

    # Create token balances for address across different block numbers
    balances = [
        AddressTokenBalances(
            address=hex_str_to_bytes("0x" + "1" * 40),
            token_address=hex_str_to_bytes("0x" + "A" * 40),
            token_type="ERC20",
            token_id=-1,
            balance=1000,
            block_number=1000,
        ),
        AddressTokenBalances(
            address=hex_str_to_bytes("0x" + "1" * 40),
            token_address=hex_str_to_bytes("0x" + "A" * 40),
            token_type="ERC20",
            token_id=-1,
            balance=1500,
            block_number=1005,  # newer block number
        ),
        AddressTokenBalances(
            address=hex_str_to_bytes("0x" + "1" * 40),
            token_address=hex_str_to_bytes("0x" + "B" * 40),
            token_type="ERC721",
            token_id=-1,
            balance=5,
            block_number=1000,
        ),
        AddressTokenBalances(
            address=hex_str_to_bytes("0x" + "1" * 40),
            token_address=hex_str_to_bytes("0x" + "C" * 40),
            token_type="ERC1155",
            token_id=2,
            balance=10,
            block_number=1000,
        ),
    ]
    session.add_all(balances)
    session.commit()

    # Current token balances for holders
    current_balances = [
        CurrentTokenBalances(
            address=hex_str_to_bytes("0x" + "1" * 40),
            token_address=hex_str_to_bytes("0x" + "A" * 40),
            balance=1500,
            token_type="ERC20",
            token_id=-1,
            block_number=1005,  # latest block for ERC20
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
    session.add_all(current_balances)
    session.commit()

    return {
        "erc20_contract": "0x" + "A" * 40,
        "erc721_contract": "0x" + "B" * 40,
        "erc1155_contract": "0x" + "C" * 40,
        "address": "0x" + "1" * 40,
    }


# -----------------------------------------------------------------------------
# Test Cases for stats_token_supply, account_token_balance, and token_info
# -----------------------------------------------------------------------------
def test_stats_token_supply(session: Session, sample_token_data):
    """Test the total supply of tokens."""
    result = stats_token_supply(session, sample_token_data["erc20_contract"])
    assert result == 1000000  # ERC20 total supply is 1000000

    result = stats_token_supply(session, sample_token_data["erc721_contract"])
    assert result == 1000  # ERC721 total supply is 1000

    result = stats_token_supply(session, sample_token_data["erc1155_contract"])
    assert result == 5000  # ERC1155 total supply is 5000


def test_account_token_balance(session: Session, sample_token_data):
    """Test getting the token balance for an address."""
    result = account_token_balance(
        session, sample_token_data["erc20_contract"], sample_token_data["address"], TokenType.ERC20
    )
    assert result == "1500"  # ERC20 balance for address is 1500 (latest block balance)

    result = account_token_balance(
        session, sample_token_data["erc721_contract"], sample_token_data["address"], TokenType.ERC721
    )
    assert result == "5"  # ERC721 balance for address is 5 (token_id=1)

    result = account_token_balance(
        session, sample_token_data["erc1155_contract"], sample_token_data["address"], TokenType.ERC1155, 2
    )
    assert result == "10"  # ERC1155 balance for address is 10 (token_id=2)


def test_account_token_balance_with_block_number(session: Session, sample_token_data):
    """Test getting token balance with a specific block number."""
    result = account_token_balance_with_block_number(
        session, sample_token_data["erc20_contract"], sample_token_data["address"], 1000, "ERC20"
    )
    assert result == "1000"  # ERC20 balance at block number 1000 is 1000

    result = account_token_balance_with_block_number(
        session, sample_token_data["erc721_contract"], sample_token_data["address"], 1000, "ERC721", -1
    )
    assert result == "5"  # ERC721 balance for token_id=1 at block number 1000 is 5

    result = account_token_balance_with_block_number(
        session, sample_token_data["erc1155_contract"], sample_token_data["address"], 1000, "ERC1155", 2
    )
    assert result == "10"  # ERC1155 balance for token_id=2 at block number 1000 is 10


def test_current_account_token_balance(session: Session, sample_token_data):
    """Test getting current token balance (latest block number)."""
    # The latest block for ERC20 has a balance of 1500
    result = account_token_balance(
        session, sample_token_data["erc20_contract"], sample_token_data["address"], TokenType.ERC20
    )
    assert result == "1500"  # Latest balance from CurrentTokenBalances for ERC20

    result = account_token_balance(
        session, sample_token_data["erc721_contract"], sample_token_data["address"], TokenType.ERC721, -1
    )
    assert result == "5"  # Latest balance for ERC721 token

    result = account_token_balance(
        session, sample_token_data["erc1155_contract"], sample_token_data["address"], TokenType.ERC1155, 2
    )
    assert result == "10"  # Latest balance for ERC1155 token


def test_token_holder_list(session: Session, sample_token_data):
    """Test getting the list of token holders."""
    result = token_holder_list(session, sample_token_data["erc20_contract"], page=1, offset=10, sort_order="desc")
    assert len(result) == 2
    assert result[0].TokenHolderAddress == "0x" + "1" * 40
    assert result[1].TokenHolderAddress == "0x" + "2" * 40


def test_token_info(session: Session, sample_token_data):
    """Test getting token information by contract address."""
    result = token_info(session, sample_token_data["erc20_contract"])
    assert result
    assert result.TokenName == "Sample ERC20"
    assert result.TokenSymbol == "SERC20"
    assert result.TokenTotalSupply == "1000000"
    assert result.TokenType == "ERC20"
    assert result.TokenDecimals == "18"

    result = token_info(session, sample_token_data["erc721_contract"])
    assert result
    assert result.TokenName == "Sample ERC721"
    assert result.TokenSymbol == "SERC721"
    assert result.TokenTotalSupply == "1000"
    assert result.TokenType == "ERC721"
    assert result.TokenDecimals is None


@pytest.fixture
def sample_nft_data(session: Session):
    """Create sample ERC721 NFT data for testing."""
    base_time = datetime(2025, 1, 1, 12, 0, 0)

    # Create ERC721 token details
    nfts = [
        ERC721TokenIdDetails(
            token_id="1", token_address=hex_str_to_bytes("0x" + "A" * 40), token_owner=hex_str_to_bytes("0x" + "1" * 40)
        ),
        ERC721TokenIdDetails(
            token_id="2", token_address=hex_str_to_bytes("0x" + "A" * 40), token_owner=hex_str_to_bytes("0x" + "1" * 40)
        ),
        ERC721TokenIdDetails(
            token_id="3", token_address=hex_str_to_bytes("0x" + "A" * 40), token_owner=hex_str_to_bytes("0x" + "2" * 40)
        ),
    ]
    session.add_all(nfts)
    session.commit()

    return {
        "contract_address": "0x" + "a" * 40,
        "address_1": "0x" + "1" * 40,
        "address_2": "0x" + "2" * 40,
    }


def test_account_address_nft_inventory(session: Session, sample_nft_data):
    """Test fetching NFT inventory for a given address."""
    result = account_address_nft_inventory(
        session=session,
        contract_address=sample_nft_data["contract_address"],
        address=sample_nft_data["address_1"],
        page=1,
        offset=10,
    )

    assert len(result) == 2
    assert result[0].tokenID == "1"
    assert result[1].tokenID == "2"


def test_account_address_nft_inventory_empty_address(session: Session):
    """Test fetching NFT inventory when no address is provided."""
    result = account_address_nft_inventory(
        session=session, contract_address="0x" + "A" * 40, address=None, page=1, offset=10
    )
    assert result == []


def test_account_address_nft_inventory_empty_contract_address(session: Session):
    """Test fetching NFT inventory when no contract address is provided."""
    result = account_address_nft_inventory(
        session=session, contract_address=None, address="0x" + "1" * 40, page=1, offset=10
    )
    assert result == []


def test_account_address_nft_inventory_pagination(session: Session, sample_nft_data):
    """Test pagination when fetching NFT inventory."""
    result_page1 = account_address_nft_inventory(
        session=session,
        contract_address=sample_nft_data["contract_address"],
        address=sample_nft_data["address_1"],
        page=1,
        offset=2,
    )
    result_page2 = account_address_nft_inventory(
        session=session,
        contract_address=sample_nft_data["contract_address"],
        address=sample_nft_data["address_1"],
        page=2,
        offset=2,
    )

    assert len(result_page1) == 2
    assert len(result_page2) == 0


def test_account_address_nft_inventory_no_tokens(session: Session, sample_nft_data):
    """Test when an address has no NFTs for a given contract address."""
    result = account_address_nft_inventory(
        session=session,
        contract_address=sample_nft_data["contract_address"],
        address=sample_nft_data["address_2"],
        page=1,
        offset=10,
    )
    assert len(result) == 1  # Only one token belonging to address_2


def test_account_address_nft_inventory_invalid_contract_address(session: Session):
    """Test fetching NFT inventory with invalid contract address."""
    result = account_address_nft_inventory(
        session=session, contract_address="0x" + "F" * 40, address="0x" + "1" * 40, page=1, offset=10
    )
    assert result == []  # No matching contract address


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
