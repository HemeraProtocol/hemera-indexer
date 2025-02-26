#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/25 14:24
# @Author  ideal93
# @File  contract_test.py.py
# @Brief

import pytest

from hemera.app.api.routes.helper.contract import _get_contract_by_address, _get_contracts_by_addresses
from hemera.common.models.contracts import Contracts
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture
def sample_contracts(session):
    contracts = [
        Contracts(
            address=hex_str_to_bytes("0x7a250d5630b4cf539739df2c5dacb4c659f2488d"),
            name="Uniswap V2 Router",
            contract_creator=hex_str_to_bytes("0x5b6c7b13a2b82ed76f48230be0c4a13f94160c5e"),
            deployed_code=b"sample bytecode 1",
            block_number=12345678,
            is_verified=True,
        ),
        Contracts(
            address=hex_str_to_bytes("0x1f9840a85d5af5bf1d1762f925bdaddc4201f984"),
            name="Uniswap Token",
            contract_creator=hex_str_to_bytes("0x4d812c19d95e76fd0194ce3c0ba2d9c04584c3e8"),
            deployed_code=b"sample bytecode 2",
            block_number=12345679,
            is_verified=True,
        ),
        Contracts(
            address=hex_str_to_bytes("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"),
            contract_creator=hex_str_to_bytes("0x8ba1f109551bd432803012645ac136ddd64dba72"),
            deployed_code=b"sample bytecode 3",
            block_number=12345680,
            is_verified=False,
        ),
    ]

    for contract in contracts:
        session.add(contract)
    session.commit()

    return contracts


def test_get_contract_by_address(session, sample_contracts):
    # Test getting existing contract with name
    contract = _get_contract_by_address(session, "0x7a250d5630b4cf539739df2c5dacb4c659f2488d")
    assert contract is not None
    assert contract.address == hex_str_to_bytes("0x7a250d5630b4cf539739df2c5dacb4c659f2488d")
    assert contract.name == "Uniswap V2 Router"
    assert contract.contract_creator == hex_str_to_bytes("0x5b6c7b13a2b82ed76f48230be0c4a13f94160c5e")

    # Test getting existing contract without name
    contract = _get_contract_by_address(session, "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2")
    assert contract is not None
    assert contract.name is None
    assert contract.contract_creator == hex_str_to_bytes("0x8ba1f109551bd432803012645ac136ddd64dba72")

    # Test getting non-existent contract
    contract = _get_contract_by_address(session, "0x0000000000000000000000000000000000000000")
    assert contract is None

    # Test getting specific columns
    contract = _get_contract_by_address(
        session, "0x7a250d5630b4cf539739df2c5dacb4c659f2488d", columns=["address", "name", "contract_creator"]
    )
    assert contract.address == hex_str_to_bytes("0x7a250d5630b4cf539739df2c5dacb4c659f2488d")
    assert contract.name == "Uniswap V2 Router"
    assert contract.contract_creator == hex_str_to_bytes("0x5b6c7b13a2b82ed76f48230be0c4a13f94160c5e")
    with pytest.raises(AttributeError):
        _ = contract.deployed_code

    # Test invalid address format
    with pytest.raises(ValueError):
        _get_contract_by_address(session, "invalid_address")


def test_get_contracts_by_addresses(session, sample_contracts):
    # Test getting multiple contracts
    addresses = [
        "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
        "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
    ]
    contracts = _get_contracts_by_addresses(session, addresses)
    assert len(contracts) == 2
    assert contracts[0].address == hex_str_to_bytes(addresses[0])
    assert contracts[0].name == "Uniswap V2 Router"
    assert contracts[1].address == hex_str_to_bytes(addresses[1])
    assert contracts[1].name == "Uniswap Token"

    # Test with mix of named and unnamed contracts
    addresses = [
        "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    ]
    contracts = _get_contracts_by_addresses(session, addresses)
    assert len(contracts) == 2
    assert contracts[0].name == "Uniswap V2 Router"
    assert contracts[1].name is None

    # Test with duplicate addresses
    addresses = [
        "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
        "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
    ]
    contracts = _get_contracts_by_addresses(session, addresses)
    assert len(contracts) == 1
    assert contracts[0].address == hex_str_to_bytes(addresses[0])

    # Test with specific columns
    contracts = _get_contracts_by_addresses(
        session, ["0x7a250d5630b4cf539739df2c5dacb4c659f2488d"], columns=["address", "name", "contract_creator"]
    )
    assert len(contracts) == 1
    assert contracts[0].name == "Uniswap V2 Router"
    assert contracts[0].contract_creator == hex_str_to_bytes("0x5b6c7b13a2b82ed76f48230be0c4a13f94160c5e")
    with pytest.raises(AttributeError):
        _ = contracts[0].deployed_code

    # Test with invalid address format
    with pytest.raises(ValueError):
        _get_contracts_by_addresses(session, ["invalid_address"])

    # Test with non-existent addresses
    addresses = [
        "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
        "0x0000000000000000000000000000000000000000",
    ]
    contracts = _get_contracts_by_addresses(session, addresses)
    assert len(contracts) == 1
    assert contracts[0].address == hex_str_to_bytes(addresses[0])


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
