#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/3 02:55
# @Author  ideal93
# @File  test_account_token_transfers.py.py
# @Brief

from datetime import datetime, timedelta
from typing import List

import pytest
from sqlalchemy import delete
from sqlmodel import Session

from hemera.app.api.routes.developer.es_adapter.helper import (
    ERC20Transfer,
    ERC721Transfer,
    ERC1155Transfer,
    get_account_token_transfers,
)
from hemera.common.enumeration.token_type import TokenType
from hemera.common.models.token_transfers import ERC20TokenTransfers, ERC721TokenTransfers, ERC1155TokenTransfers
from hemera.common.models.tokens import Tokens
from hemera.common.models.transactions import Transactions
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture(autouse=True)
def clean_db(session: Session):
    """
    Clean the database before each test by deleting from transfers, tokens, and transactions.
    """
    # Delete from token transfer tables
    session.exec(delete(ERC20TokenTransfers))
    session.exec(delete(ERC721TokenTransfers))
    session.exec(delete(ERC1155TokenTransfers))
    # Delete from tokens and transactions tables
    session.exec(delete(Tokens))
    session.exec(delete(Transactions))
    session.commit()


@pytest.fixture
def sample_erc20_data(session: Session):
    """
    Create sample ERC20 token transfers, tokens, and transactions.
    """
    # Use fixed addresses for testing
    sample_token_address = "0x" + "a" * 40
    sample_account_address = "0x" + "b" * 40
    base_time = datetime(2025, 1, 1, 12, 0, 0)

    # Create a token record for the ERC20 token
    token = Tokens(address=hex_str_to_bytes(sample_token_address), name="SampleERC20", symbol="SERC20", decimals=18)
    session.add(token)
    session.commit()

    # Create 5 transactions and corresponding ERC20 transfer records.
    for i in range(5):
        tx_hash = hex_str_to_bytes(f"0x{i:064x}")
        block_number = 1000 + i
        tx = Transactions(
            hash=tx_hash,
            block_number=block_number,
            block_timestamp=base_time + timedelta(minutes=i),
            nonce=i,
            block_hash=hex_str_to_bytes(f"0x{i:064x}"),
            input=None,
            transaction_index=i,
            from_address=hex_str_to_bytes(sample_account_address) if i % 2 == 0 else hex_str_to_bytes("0x" + "c" * 40),
            to_address=hex_str_to_bytes("0x" + "c" * 40) if i % 2 == 0 else hex_str_to_bytes(sample_account_address),
            value=1000000 * (i + 1),
            gas=21000,
            gas_price=20000000000,
            receipt_status=1,
            receipt_contract_address=None,
            receipt_cumulative_gas_used=21000 * (i + 1),
            receipt_gas_used=21000,
        )
        session.add(tx)
        # Create corresponding ERC20 transfer record
        transfer = ERC20TokenTransfers(
            block_number=block_number,
            log_index=i,
            block_timestamp=tx.block_timestamp,
            transaction_hash=tx_hash,
            block_hash=tx.block_hash,
            from_address=tx.from_address,
            to_address=tx.to_address,
            token_address=hex_str_to_bytes(sample_token_address),
            value=1000 * (i + 1),  # some arbitrary value
        )
        session.add(transfer)
    session.commit()
    return {
        "token_address": sample_token_address,
        "account_address": sample_account_address,
        "base_time": base_time,
    }


@pytest.fixture
def sample_erc721_data(session: Session):
    """
    Create sample ERC721 token transfers, tokens, and transactions.
    """
    sample_token_address = "0x" + "d" * 40
    sample_account_address = "0x" + "e" * 40
    base_time = datetime(2025, 1, 2, 12, 0, 0)

    # Create a token record for the ERC721 token
    token = Tokens(
        address=hex_str_to_bytes(sample_token_address),
        name="SampleERC721",
        symbol="SERC721",
        decimals=0,  # not used for ERC721 transfers
    )
    session.add(token)
    session.commit()

    # Create 3 transactions and corresponding ERC721 transfer records.
    for i in range(3):
        tx_hash = hex_str_to_bytes(f"0x{(10+i):064x}")
        block_number = 2000 + i
        tx = Transactions(
            hash=tx_hash,
            block_number=block_number,
            block_timestamp=base_time + timedelta(minutes=i),
            nonce=i,
            block_hash=hex_str_to_bytes(f"0x{(10+i):064x}"),
            input=None,
            transaction_index=i,
            from_address=hex_str_to_bytes(sample_account_address) if i % 2 == 0 else hex_str_to_bytes("0x" + "f" * 40),
            to_address=hex_str_to_bytes("0x" + "f" * 40) if i % 2 == 0 else hex_str_to_bytes(sample_account_address),
            value=0,  # ERC721 transfers typically do not use a value field
            gas=30000,
            gas_price=25000000000,
            receipt_status=1,
            receipt_contract_address=None,
            receipt_cumulative_gas_used=30000 * (i + 1),
            receipt_gas_used=30000,
        )
        session.add(tx)
        # Create corresponding ERC721 transfer record with token_id
        transfer = ERC721TokenTransfers(
            block_number=block_number,
            block_timestamp=tx.block_timestamp,
            transaction_hash=tx_hash,
            log_index=i,
            block_hash=tx.block_hash,
            from_address=tx.from_address,
            to_address=tx.to_address,
            token_address=hex_str_to_bytes(sample_token_address),
            token_id=i,  # simple token_id
        )
        session.add(transfer)
    session.commit()
    return {
        "token_address": sample_token_address,
        "account_address": sample_account_address,
        "base_time": base_time,
    }


@pytest.fixture
def sample_erc1155_data(session: Session):
    """
    Create sample ERC1155 token transfers, tokens, and transactions.
    """
    sample_token_address = "0x" + "1" * 40
    sample_account_address = "0x" + "2" * 40
    base_time = datetime(2025, 1, 3, 12, 0, 0)

    # Create a token record for the ERC1155 token
    token = Tokens(
        address=hex_str_to_bytes(sample_token_address),
        name="SampleERC1155",
        symbol="SERC1155",
        decimals=0,  # decimals not applicable for ERC1155 transfers
    )
    session.add(token)
    session.commit()

    # Create 4 transactions and corresponding ERC1155 transfer records.
    for i in range(4):
        tx_hash = hex_str_to_bytes(f"0x{(20+i):064x}")
        block_number = 3000 + i
        tx = Transactions(
            hash=tx_hash,
            block_number=block_number,
            block_timestamp=base_time + timedelta(minutes=i),
            nonce=i,
            block_hash=hex_str_to_bytes(f"0x{(20+i):064x}"),
            input=None,
            transaction_index=i,
            from_address=hex_str_to_bytes(sample_account_address) if i % 2 == 0 else hex_str_to_bytes("0x" + "3" * 40),
            to_address=hex_str_to_bytes("0x" + "3" * 40) if i % 2 == 0 else hex_str_to_bytes(sample_account_address),
            value=0,
            gas=25000,
            gas_price=22000000000,
            receipt_status=1,
            receipt_contract_address=None,
            receipt_cumulative_gas_used=25000 * (i + 1),
            receipt_gas_used=25000,
        )
        session.add(tx)
        # Create corresponding ERC1155 transfer record with token_id and value
        transfer = ERC1155TokenTransfers(
            block_number=block_number,
            block_timestamp=tx.block_timestamp,
            transaction_hash=tx_hash,
            log_index=i,
            block_hash=tx.block_hash,
            from_address=tx.from_address,
            to_address=tx.to_address,
            token_address=hex_str_to_bytes(sample_token_address),
            token_id=i,  # token id for ERC1155
            value=500 * (i + 1),  # arbitrary value transferred
        )
        session.add(transfer)
    session.commit()
    return {
        "token_address": sample_token_address,
        "account_address": sample_account_address,
        "base_time": base_time,
    }


def test_returns_empty_when_no_address_or_contract(session: Session):
    """
    Test that the function returns an empty list if both address and contract_address are None.
    """
    results = get_account_token_transfers(
        session=session,
        contract_address=None,
        address=None,
        page=1,
        offset=10,
        sort_order="desc",
        start_block=0,
        end_block=10000,
        token_type=TokenType.ERC20,
    )
    assert results == []


def test_filters_by_address_erc20(session: Session, sample_erc20_data):
    """
    Test filtering ERC20 transfers by account address.
    """
    # Use the sample account address that appears in some transfers.
    account_address = sample_erc20_data["account_address"]
    results: List[ERC20Transfer] = get_account_token_transfers(
        session=session,
        contract_address=None,
        address=account_address,
        page=1,
        offset=10,
        sort_order="asc",  # ascending order so the lowest block_number comes first
        start_block=1000,
        end_block=1010,
        token_type=TokenType.ERC20,
    )

    # From our fixture, out of 5 transfers, 3 should have the account address (either in from or to)
    # depending on how we alternated the addresses.
    assert len(results) >= 1
    # Check that every returned transfer has the account address in either from or to fields.
    for transfer in results:
        from_addr = transfer.from_address
        to_addr = transfer.to
        expected = account_address.lower()
        # Convert to lower-case hex strings for comparison.
        assert expected in (from_addr.lower(), to_addr.lower())
    # Also check that pagination and sort order work correctly.
    block_numbers = [int(t.block_number) for t in results]
    assert block_numbers == sorted(block_numbers)


def test_filters_by_contract_address_erc20(session: Session, sample_erc20_data):
    """
    Test filtering ERC20 transfers by contract (token) address.
    """
    token_address = sample_erc20_data["token_address"]
    results: List[ERC20Transfer] = get_account_token_transfers(
        session=session,
        contract_address=token_address,
        address=None,
        page=1,
        offset=10,
        sort_order="desc",
        start_block=1000,
        end_block=1010,
        token_type=TokenType.ERC20,
    )
    # We expect to get all 5 transfers for this token
    assert len(results) == 5
    for transfer in results:
        assert transfer.contract_address.lower() == token_address.lower()


def test_pagination_erc20(session: Session, sample_erc20_data):
    """
    Test that pagination returns the correct subset of ERC20 transfers.
    """
    # Assume our fixture inserted 5 transfers. Set offset=2 so we need 3 pages.
    # Page 1: transfers 0-1; Page 2: transfers 2-3; Page 3: transfer 4.
    token_address = sample_erc20_data["token_address"]
    # Page 1 (descending order)
    results_page1 = get_account_token_transfers(
        session=session,
        contract_address=token_address,
        address=None,
        page=1,
        offset=2,
        sort_order="desc",
        start_block=1000,
        end_block=1010,
        token_type=TokenType.ERC20,
    )
    assert len(results_page1) == 2
    # Page 3
    results_page3 = get_account_token_transfers(
        session=session,
        contract_address=token_address,
        address=None,
        page=3,
        offset=2,
        sort_order="desc",
        start_block=1000,
        end_block=1010,
        token_type=TokenType.ERC20,
    )
    # Page 3 should have the remaining 1 record
    assert len(results_page3) == 1


def test_sort_order_erc20(session: Session, sample_erc20_data):
    """
    Test that sort order is applied correctly for ERC20 transfers.
    """
    token_address = sample_erc20_data["token_address"]

    # Descending order: highest block number first
    results_desc = get_account_token_transfers(
        session=session,
        contract_address=token_address,
        address=None,
        page=1,
        offset=10,
        sort_order="desc",
        start_block=1000,
        end_block=1010,
        token_type=TokenType.ERC20,
    )
    block_numbers_desc = [int(t.block_number) for t in results_desc]
    assert block_numbers_desc == sorted(block_numbers_desc, reverse=True)

    # Ascending order: lowest block number first
    results_asc = get_account_token_transfers(
        session=session,
        contract_address=token_address,
        address=None,
        page=1,
        offset=10,
        sort_order="asc",
        start_block=1000,
        end_block=1010,
        token_type=TokenType.ERC20,
    )
    block_numbers_asc = [int(t.block_number) for t in results_asc]
    assert block_numbers_asc == sorted(block_numbers_asc)


def test_token_type_specific_fields_erc721(session: Session, sample_erc721_data):
    """
    Test that token type specific fields (like tokenID) are returned correctly for ERC721.
    """
    account_address = sample_erc721_data["account_address"]
    token_address = sample_erc721_data["token_address"]

    results: List[ERC721Transfer] = get_account_token_transfers(
        session=session,
        contract_address=token_address,
        address=account_address,
        page=1,
        offset=10,
        sort_order="asc",
        start_block=2000,
        end_block=2020,
        token_type=TokenType.ERC721,
    )
    # There are 3 transfers in our fixture. Each transfer should have a tokenID field.
    assert len(results) <= 3
    for transfer in results:
        # tokenID was set to i in our fixture (0, 1, 2)
        assert hasattr(transfer, "token_id")
        # Also check that tokenName and tokenSymbol are set correctly.
        assert transfer.token_name == "SampleERC721"
        assert transfer.token_symbol == "SERC721"


def test_token_type_specific_fields_erc1155(session: Session, sample_erc1155_data):
    """
    Test that token type specific fields (like tokenValue and tokenID) are returned correctly for ERC1155.
    """
    account_address = sample_erc1155_data["account_address"]
    token_address = sample_erc1155_data["token_address"]

    results: List[ERC1155Transfer] = get_account_token_transfers(
        session=session,
        contract_address=token_address,
        address=account_address,
        page=1,
        offset=10,
        sort_order="asc",
        start_block=3000,
        end_block=3020,
        token_type=TokenType.ERC1155,
    )
    # There are 4 transfers in our fixture.
    assert len(results) <= 4
    for transfer in results:
        # tokenID and tokenValue should be available for ERC1155 transfers.
        assert hasattr(transfer, "token_id")
        assert hasattr(transfer, "token_value")
        # Also check that tokenName and tokenSymbol are set correctly.
        assert transfer.token_name == "SampleERC1155"
        assert transfer.token_symbol == "SERC1155"


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
