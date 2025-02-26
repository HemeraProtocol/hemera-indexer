#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/4 12:37
# @Author  ideal93
# @File  test_blocks.py
# @Brief

import pytest
from sqlmodel import Session, delete

from hemera.app.api.routes.developer.es_adapter.helper import get_contract_creator_and_creation_tx_hash
from hemera.common.models.contracts import Contracts
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture(autouse=True)
def clean_db(session: Session):
    session.exec(delete(Contracts))
    session.commit()


@pytest.fixture
def sample_contract_data(session: Session):
    """Create sample contract data for testing."""
    contracts = [
        Contracts(
            address=hex_str_to_bytes("0x" + "A" * 40),
            contract_creator=hex_str_to_bytes("0x" + "B" * 40),
            transaction_hash=hex_str_to_bytes("0x" + "C" * 64),
        ),
        Contracts(
            address=hex_str_to_bytes("0x" + "D" * 40),
            contract_creator=hex_str_to_bytes("0x" + "E" * 40),
            transaction_hash=hex_str_to_bytes("0x" + "F" * 64),
        ),
    ]
    session.add_all(contracts)
    session.commit()

    return {
        "contract_1": "0x" + "a" * 40,
        "contract_2": "0x" + "d" * 40,
    }


def test_get_contract_creator_and_creation_tx_hash(session: Session, sample_contract_data):
    """Test retrieving contract creator and transaction hash."""
    result = get_contract_creator_and_creation_tx_hash(
        session=session, contract_addresses=[sample_contract_data["contract_1"], sample_contract_data["contract_2"]]
    )

    assert len(result) == 2
    assert result[0].contractAddress == sample_contract_data["contract_1"]
    assert result[0].contractCreator == "0x" + "b" * 40
    assert result[0].txHash == "0x" + "c" * 64

    assert result[1].contractAddress == sample_contract_data["contract_2"]
    assert result[1].contractCreator == "0x" + "e" * 40
    assert result[1].txHash == "0x" + "f" * 64


def test_get_contract_creator_and_creation_tx_hash_empty_input(session: Session):
    """Test with an empty list of contract addresses."""
    result = get_contract_creator_and_creation_tx_hash(session=session, contract_addresses=[])
    assert result == []


def test_get_contract_creator_and_creation_tx_hash_invalid_address(session: Session):
    """Test with an invalid contract address."""
    result = get_contract_creator_and_creation_tx_hash(session=session, contract_addresses=["0x" + "f" * 40])
    assert result == []  # No matching contract address


def test_get_contract_creator_and_creation_tx_hash_single_address(session: Session, sample_contract_data):
    """Test with a single contract address."""
    result = get_contract_creator_and_creation_tx_hash(
        session=session, contract_addresses=[sample_contract_data["contract_1"]]
    )
    assert len(result) == 1
    assert result[0].contractAddress == sample_contract_data["contract_1"]
    assert result[0].contractCreator == "0x" + "b" * 40
    assert result[0].txHash == "0x" + "c" * 64


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
