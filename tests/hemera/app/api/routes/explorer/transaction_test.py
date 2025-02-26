#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/24 16:02
# @Author  ideal93
# @File  transaction_test.py
# @Brief

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from hemera.app.core.config import settings
from hemera.common.enumeration.txn_type import AddressNftTransferType, AddressTokenTransferType, AddressTransactionType
from hemera.common.models.address.address_nft_transfers import AddressNftTransfers
from hemera.common.models.address.address_token_transfers import AddressTokenTransfers
from hemera.common.models.address.address_transactions import AddressTransactions
from hemera.common.models.blocks import Blocks
from hemera.common.models.contracts import Contracts
from hemera.common.models.token_transfers import (
    ERC20TokenTransfers,
    ERC721TokenTransfers,
    ERC1155TokenTransfers,
    NftTransfers,
)
from hemera.common.models.tokens import Tokens
from hemera.common.models.traces import ContractInternalTransactions
from hemera.common.models.transactions import Transactions
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture
def sample_addresses():
    return {
        "sender": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "receiver": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "token": "0xcccccccccccccccccccccccccccccccccccccccc",
    }


@pytest.fixture
def sample_contracts(session):
    contracts = [
        Contracts(
            address=hex_str_to_bytes("0x0000000000000000000000000000000000000008"),
            name="Uniswap V2 Router",
            contract_creator=hex_str_to_bytes("0x5b6c7b13a2b82ed76f48230be0c4a13f94160c5e"),
            deployed_code=b"sample bytecode 1",
            block_number=12345678,
            is_verified=True,
        ),
        Contracts(
            address=hex_str_to_bytes("0x0000000000000000000000000000000000000009"),
            name="Uniswap Token",
            contract_creator=hex_str_to_bytes("0x4d812c19d95e76fd0194ce3c0ba2d9c04584c3e8"),
            deployed_code=b"sample bytecode 2",
            block_number=12345679,
            is_verified=False,
        ),
    ]

    for contract in contracts:
        session.add(contract)
    session.commit()

    return contracts


@pytest.fixture
def sample_tokens(session, sample_addresses):
    tokens = [
        Tokens(
            address=hex_str_to_bytes(sample_addresses["token"]),
            name="Wrapped Ether",
            symbol="WETH",
            token_type="ERC20",
            decimals=18,
            price=Decimal("1000"),
            previous_price=Decimal("900"),
            logo_url="https://example.com/logo.png",
            market_cap=Decimal("1000000"),
            on_chain_market_cap=Decimal("2000000"),
        )
    ]
    session.add(tokens[0])
    session.commit()
    return tokens


@pytest.fixture
def erc20_token_transfers(session, sample_addresses, sample_tokens):
    """Create sample ERC20 token transfers"""
    now = datetime.utcnow()
    transfers = [
        ERC20TokenTransfers(
            transaction_hash=hex_str_to_bytes("0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            block_number=21436149,
            block_timestamp=now,
            from_address=hex_str_to_bytes(sample_addresses["sender"]),
            to_address=hex_str_to_bytes(sample_addresses["receiver"]),
            token_address=hex_str_to_bytes(sample_addresses["token"]),
            value=Decimal("1000000000000000000"),  # 1 token
            log_index=0,
            block_hash=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb1"),
        ),
        ERC20TokenTransfers(
            transaction_hash=hex_str_to_bytes("0x2234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            block_number=21436149,
            block_timestamp=now,
            from_address=hex_str_to_bytes(sample_addresses["sender"]),
            to_address=hex_str_to_bytes(sample_addresses["receiver"]),
            token_address=hex_str_to_bytes(sample_addresses["token"]),
            value=Decimal("2000000000000000000"),  # 2 tokens
            log_index=1,
            block_hash=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb1"),
        ),
    ]

    for transfer in transfers:
        session.add(transfer)
    session.commit()
    return transfers


@pytest.fixture
def erc721_token_transfers(session, sample_addresses):
    """Create sample ERC721 token transfers"""
    now = datetime.utcnow()
    transfers = [
        ERC721TokenTransfers(
            transaction_hash=hex_str_to_bytes("0x3234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            block_number=21436149,
            block_timestamp=now,
            from_address=hex_str_to_bytes(sample_addresses["sender"]),
            to_address=hex_str_to_bytes(sample_addresses["receiver"]),
            token_address=hex_str_to_bytes(sample_addresses["token"]),
            token_id=Decimal("1"),
            log_index=0,
            block_hash=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb2"),
        ),
        ERC721TokenTransfers(
            transaction_hash=hex_str_to_bytes("0x4234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            block_number=21436148,
            block_timestamp=now - timedelta(minutes=2),
            from_address=hex_str_to_bytes(sample_addresses["receiver"]),
            to_address=hex_str_to_bytes(sample_addresses["sender"]),
            token_address=hex_str_to_bytes(sample_addresses["token"]),
            token_id=Decimal("2"),
            log_index=0,
            block_hash=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb3"),
        ),
    ]

    for transfer in transfers:
        session.add(transfer)
    session.commit()
    return transfers


@pytest.fixture
def erc1155_token_transfers(session, sample_addresses):
    """Create sample ERC1155 token transfers"""
    now = datetime.utcnow()
    transfers = [
        ERC1155TokenTransfers(
            transaction_hash=hex_str_to_bytes("0x5234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            block_number=21436149,
            block_timestamp=now,
            from_address=hex_str_to_bytes(sample_addresses["sender"]),
            to_address=hex_str_to_bytes(sample_addresses["receiver"]),
            token_address=hex_str_to_bytes(sample_addresses["token"]),
            token_id=Decimal("1"),
            value=Decimal("5"),
            log_index=0,
            block_hash=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb4"),
        ),
        ERC1155TokenTransfers(
            transaction_hash=hex_str_to_bytes("0x6234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            block_number=21436148,
            block_timestamp=now - timedelta(minutes=1),
            from_address=hex_str_to_bytes(sample_addresses["sender"]),
            to_address=hex_str_to_bytes(sample_addresses["receiver"]),
            token_address=hex_str_to_bytes(sample_addresses["token"]),
            token_id=Decimal("2"),
            value=Decimal("10"),
            log_index=0,
            block_hash=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb5"),
        ),
    ]

    for transfer in transfers:
        session.add(transfer)
    session.commit()
    return transfers


@pytest.fixture
def nft_transfers(session, sample_addresses):
    """Create sample NFT transfers in unified table"""
    now = datetime.utcnow()
    transfers = [
        NftTransfers(
            transaction_hash=hex_str_to_bytes("0x7234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            block_number=21436149,
            block_timestamp=now,
            from_address=hex_str_to_bytes(sample_addresses["sender"]),
            to_address=hex_str_to_bytes(sample_addresses["receiver"]),
            token_address=hex_str_to_bytes(sample_addresses["token"]),
            token_id=Decimal("1"),
            value=None,  # ERC721
            log_index=0,
            block_hash=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb6"),
        ),
        NftTransfers(
            transaction_hash=hex_str_to_bytes("0x8234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            block_number=21436148,
            block_timestamp=now - timedelta(minutes=1),
            from_address=hex_str_to_bytes(sample_addresses["sender"]),
            to_address=hex_str_to_bytes(sample_addresses["receiver"]),
            token_address=hex_str_to_bytes(sample_addresses["token"]),
            token_id=Decimal("2"),
            value=Decimal("5"),  # ERC1155
            log_index=0,
            block_hash=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb7"),
        ),
    ]

    for transfer in transfers:
        session.add(transfer)
    session.commit()
    return transfers


@pytest.fixture
def address_token_transfers(session, sample_addresses):
    """Create sample address token transfers"""
    now = datetime.utcnow()
    transfers = [
        AddressTokenTransfers(
            address=hex_str_to_bytes(sample_addresses["sender"]),
            block_number=21436149,
            block_timestamp=now,
            transaction_hash=hex_str_to_bytes("0x9234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            token_address=hex_str_to_bytes(sample_addresses["token"]),
            related_address=hex_str_to_bytes(sample_addresses["receiver"]),
            transfer_type=AddressTokenTransferType.SENDER.value,
            value=Decimal("1000000000000000000"),
            log_index=0,
            block_hash=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb8"),
        ),
        AddressTokenTransfers(
            address=hex_str_to_bytes(sample_addresses["receiver"]),
            block_number=21436148,
            block_timestamp=now - timedelta(minutes=1),
            transaction_hash=hex_str_to_bytes("0xa234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            token_address=hex_str_to_bytes(sample_addresses["token"]),
            related_address=hex_str_to_bytes(sample_addresses["sender"]),
            transfer_type=AddressTokenTransferType.RECEIVER.value,
            value=Decimal("500000000000000000"),
            log_index=0,
            block_hash=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb9"),
        ),
    ]

    for transfer in transfers:
        session.add(transfer)
    session.commit()
    return transfers


@pytest.fixture
def address_nft_transfers(session, sample_addresses):
    """Create sample address NFT transfers"""
    now = datetime.utcnow()
    transfers = [
        AddressNftTransfers(
            address=hex_str_to_bytes(sample_addresses["sender"]),
            block_number=21436149,
            block_timestamp=now,
            transaction_hash=hex_str_to_bytes("0xb234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            token_address=hex_str_to_bytes(sample_addresses["token"]),
            related_address=hex_str_to_bytes(sample_addresses["receiver"]),
            transfer_type=AddressNftTransferType.SENDER.value,
            token_id=Decimal("1"),
            value=None,  # ERC721
            log_index=0,
            block_hash=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb10"),
        ),
        AddressNftTransfers(
            address=hex_str_to_bytes(sample_addresses["receiver"]),
            block_number=21436148,
            block_timestamp=now - timedelta(minutes=1),
            transaction_hash=hex_str_to_bytes("0xc234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
            token_address=hex_str_to_bytes(sample_addresses["token"]),
            related_address=hex_str_to_bytes(sample_addresses["sender"]),
            transfer_type=AddressNftTransferType.RECEIVER.value,
            token_id=Decimal("2"),
            value=Decimal("5"),  # ERC1155
            log_index=0,
            block_hash=hex_str_to_bytes("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb11"),
        ),
    ]

    for transfer in transfers:
        session.add(transfer)
    session.commit()
    return transfers


@pytest.mark.serial
@pytest.fixture
def sample_internal_transactions(clean_db, sample_contracts, session):
    """Create a set of test internal transactions"""
    transactions = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    # Create 10 internal transactions
    for i in range(10):
        tx = ContractInternalTransactions(
            trace_id=f"trace_{i}",
            trace_type="call",
            call_type="call",
            value=str(1000000000000000000 * (i + 1)),  # 1-10 ETH
            error=None if i < 8 else "Reverted",
            status=1 if i < 8 else 0,
            block_number=1000 + i,
            block_timestamp=base_time + timedelta(minutes=i),
            transaction_hash=bytes.fromhex(f"{i:064x}"),
            from_address=bytes.fromhex(f"{i:040x}"),
            to_address=bytes.fromhex(f"{i + 1:040x}"),
        )
        transactions.append(tx)
        session.add(tx)

    # Create some transactions with same block number for block filtering test
    for i in range(3):
        tx = ContractInternalTransactions(
            trace_id=f"trace_block_{i}",
            trace_type="call",
            call_type="call",
            value=str(500000000000000000 * (i + 1)),  # 0.5-1.5 ETH
            error=None,
            status=1,
            block_number=1005,  # Same block number
            block_timestamp=base_time + timedelta(minutes=10, seconds=i * 15),
            transaction_hash=bytes.fromhex(f"aa{i:062x}"),
            from_address=bytes.fromhex(f"bb{i:038x}"),
            to_address=bytes.fromhex(f"cc{i:038x}"),
        )
        transactions.append(tx)
        session.add(tx)

    session.commit()
    return transactions


@pytest.mark.serial
@pytest.fixture
def sample_transactions(clean_db, session):
    """Create a set of test transactions"""
    transactions = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    # Create blocks for transactions
    blocks = []
    for i in range(5):
        block = Blocks(
            number=1000 + i,
            hash=bytes.fromhex(f"bb{i:062x}"),
            timestamp=base_time + timedelta(minutes=i),
            parent_hash=bytes.fromhex(f"{i - 1:064x}") if i > 0 else bytes(32),
            gas_limit="15000000",
            gas_used=f"{5000000 + i * 100000}",
            base_fee_per_gas="1000000000",
            miner=bytes.fromhex(f"{i:040x}"),
            transactions_count=2,  # Each block has 2 transactions
            internal_transactions_count=0,
            reorg=False,
        )
        blocks.append(block)
        session.add(block)

    # Create 2 transactions for each block
    for block in blocks:
        for j in range(2):
            tx = Transactions(
                hash=bytes.fromhex(f"aa{block.number:012x}{j:050x}"),
                block_number=block.number,
                block_hash=block.hash,
                block_timestamp=block.timestamp,
                transaction_index=j,
                from_address=bytes.fromhex(f"{j:040x}"),
                to_address=bytes.fromhex(f"{j + 1:040x}"),
                value=str(1000000000000000000 * (j + 1)),  # 1-2 ETH
                gas="21000",
                gas_price="1000000000",
                transaction_type=0,
                method_id=None,
                input=None,
                max_fee_per_gas=None,
                max_priority_fee_per_gas=None,
                receipt_status=1,
                receipt_gas_used="21000",
            )
            transactions.append(tx)

            address_transaction_1 = AddressTransactions(
                address=bytes.fromhex(f"{j:040x}"),
                block_number=block.number,
                transaction_index=j,
                block_timestamp=block.timestamp,
                transaction_hash=bytes.fromhex(f"aa{block.number:012x}{j:050x}"),
                block_hash=block.hash,
                txn_type=AddressTransactionType.SENDER.value,
                related_address=bytes.fromhex(f"{j + 1:040x}"),
                value=Decimal("1000000000000000000"),
                transaction_fee=Decimal("21000") * Decimal("21000"),
                receipt_status=1,
                method=None,
            )
            address_transaction_2 = AddressTransactions(
                address=bytes.fromhex(f"{j + 1:040x}"),
                block_number=block.number,
                transaction_index=j,
                block_timestamp=block.timestamp,
                transaction_hash=bytes.fromhex(f"aa{block.number:012x}{j:050x}"),
                block_hash=block.hash,
                txn_type=AddressTransactionType.RECEIVER.value,
                related_address=bytes.fromhex(f"{j:040x}"),
                value=Decimal("1000000000000000000"),
                transaction_fee=Decimal("21000") * Decimal("21000"),
                receipt_status=1,
                method=None,
            )
            session.add(address_transaction_1)
            session.add(address_transaction_2)
            session.add(tx)

    session.commit()
    return transactions


@pytest.mark.serial
@pytest.mark.api
def test_get_internal_transactions_success(client, sample_internal_transactions, session):
    """Test successful retrieval of internal transactions with default pagination"""
    response = client.get("/v1/explorer/internal_transactions")
    print(response.json())
    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 1
    assert data["size"] == 25
    assert data["total"] == 13  # 10 regular + 3 same block transactions
    assert len(data["data"]) == 13

    # Verify first transaction data
    first_tx = data["data"][0]
    assert first_tx["trace_id"] == "trace_9"
    assert first_tx["trace_type"] == "call"
    assert first_tx["from_addr"]["is_contract"] == True
    assert first_tx["to_addr"]["is_contract"] == False
    assert first_tx["display_value"] == "10"
    assert first_tx["value"] == "10000000000000000000"
    assert first_tx["status"] == 0
    assert first_tx["error"] == "Reverted"


@pytest.mark.serial
@pytest.mark.api
def test_get_internal_transactions_with_pagination(client, sample_internal_transactions, session):
    """Test internal transactions retrieval with custom pagination"""
    response = client.get("/v1/explorer/internal_transactions?page=2&size=5")

    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 2
    assert data["size"] == 5
    assert len(data["data"]) == 5


@pytest.mark.serial
@pytest.mark.api
def test_get_internal_transactions_by_address(client, sample_internal_transactions, session):
    """Test internal transactions retrieval filtered by address"""
    # Test with 'from' address
    address = "0x" + "0" * 39 + "1"  # First transaction's from_address
    response = client.get(f"/v1/explorer/internal_transactions?address={address}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    assert any(tx["from_address"] == address for tx in data["data"])

    # Test with 'to' address
    address = "0x" + "0" * 39 + "2"  # First transaction's to_address
    response = client.get(f"/v1/explorer/internal_transactions?address={address}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    assert any(tx["to_address"] == address for tx in data["data"])


@pytest.mark.serial
@pytest.mark.api
def test_get_internal_transactions_by_block(client, sample_internal_transactions, session):
    """Test internal transactions retrieval filtered by block number"""
    response = client.get("/v1/explorer/internal_transactions?block=1005")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 4  # 1 regular + 3 same block transactions
    assert all(tx["block_number"] == 1005 for tx in data["data"])


@pytest.mark.serial
@pytest.mark.api
def test_get_internal_transactions_invalid_pagination(client, sample_internal_transactions):
    """Test internal transactions retrieval with invalid pagination parameters"""
    # Test negative page
    response = client.get("/v1/explorer/internal_transactions?page=0")
    assert response.status_code == 422

    # Test negative size
    response = client.get("/v1/explorer/internal_transactions?size=0")
    assert response.status_code == 422


@pytest.mark.serial
@pytest.mark.api
def test_get_internal_transactions_empty_db(client, clean_db):
    """Test internal transactions retrieval with empty database"""
    response = client.get("/v1/explorer/internal_transactions")

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert len(data["data"]) == 0
    assert data["page"] == 1
    assert data["size"] == 25


@pytest.mark.serial
@pytest.mark.api
def test_get_internal_transactions_response_structure(client, sample_internal_transactions):
    """Test the structure of internal transaction response data"""
    response = client.get("/v1/explorer/internal_transactions")

    assert response.status_code == 200
    data = response.json()

    # Check first transaction has all required fields
    first_tx = data["data"][0]
    required_fields = {
        "trace_id",
        "trace_type",
        "call_type",
        "value",
        "error",
        "status",
        "block_number",
        "block_timestamp",
        "transaction_hash",
        "from_address",
        "to_address",
        "from_addr",
        "to_addr",
        "display_value",
    }

    assert all(field in first_tx for field in required_fields)
    assert isinstance(first_tx["trace_id"], str)
    assert isinstance(first_tx["block_number"], int)
    assert isinstance(first_tx["status"], int)


@pytest.mark.serial
@pytest.mark.api
def test_get_internal_transactions_max_limit(client, sample_internal_transactions):
    """Test internal transactions retrieval with pagination exceeding max limit"""
    max_page = settings.MAX_INTERNAL_TRANSACTION // 25 + 1
    response = client.get(f"/v1/explorer/internal_transactions?page={max_page}&size=25")

    assert response.status_code == 400
    assert str(settings.MAX_INTERNAL_TRANSACTION) in response.json()["detail"]


@pytest.mark.serial
@pytest.mark.api
def test_get_transactions_success(client, sample_transactions, session):
    """Test successful retrieval of transactions with default pagination"""
    response = client.get("/v1/explorer/transactions")

    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 1
    assert data["size"] == 25
    assert data["total"] == 10  # 5 blocks * 2 transactions
    assert len(data["data"]) == 10

    # Verify first transaction data
    first_tx = data["data"][0]
    assert first_tx["block_number"] == 1004  # Latest block
    assert isinstance(first_tx["value"], str)
    assert isinstance(first_tx["transaction_fee"], str)
    assert isinstance(first_tx["value_usd"], str)
    assert isinstance(first_tx["transaction_fee_usd"], str)


@pytest.mark.serial
@pytest.mark.api
def test_get_transactions_by_block(client, sample_transactions, session):
    """Test transactions retrieval filtered by block"""
    # Test by block number
    response = client.get("/v1/explorer/transactions?block=1000")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["data"]) == 2
    assert all(tx["block_number"] == 1000 for tx in data["data"])

    # Test by block hash
    block_hash = "0x" + "bb" + "0" * 62
    response = client.get(f"/v1/explorer/transactions?block={block_hash}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["data"]) == 2
    assert all(tx["block_number"] == 1000 for tx in data["data"])


@pytest.mark.serial
@pytest.mark.api
def test_get_transactions_by_address(client, sample_transactions, session):
    """Test transactions retrieval filtered by address"""
    # Test with 'from' address
    address = "0x" + "0" * 40
    response = client.get(f"/v1/explorer/transactions?address={address}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    assert any(tx["from_address"] == address for tx in data["data"])

    # Test with 'to' address
    address = "0x" + "0" * 39 + "1"
    response = client.get(f"/v1/explorer/transactions?address={address}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    assert any(tx["to_address"] == address for tx in data["data"])


@pytest.mark.serial
@pytest.mark.api
def test_get_transactions_by_date(client, sample_transactions, session):
    """Test transactions retrieval filtered by date"""
    response = client.get("/v1/explorer/transactions?date=20240101")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0

    first_tx = data["data"][0]
    tx_date = datetime.fromisoformat(first_tx["block_timestamp"]).strftime("%Y%m%d")
    assert tx_date == "20240101"


@pytest.mark.serial
@pytest.mark.api
def test_get_transactions_invalid_block(client, sample_transactions):
    """Test transactions retrieval with invalid block parameter"""
    # Test invalid block number
    response = client.get("/v1/explorer/transactions?block=9999999")
    assert response.status_code == 400

    # Test invalid block hash
    response = client.get("/v1/explorer/transactions?block=0xinvalid")
    assert response.status_code == 400


@pytest.mark.serial
@pytest.mark.api
def test_get_transactions_invalid_date(client, sample_transactions):
    """Test transactions retrieval with invalid date parameter"""
    # Test invalid date format
    response = client.get("/v1/explorer/transactions?date=2024-01-01")
    assert response.status_code == 400

    # Test invalid date value
    response = client.get("/v1/explorer/transactions?date=20241301")
    assert response.status_code == 400


@pytest.mark.serial
@pytest.mark.api
def test_get_transactions_with_pagination(client, sample_transactions, session):
    """Test transactions retrieval with custom pagination"""
    response = client.get("/v1/explorer/transactions?page=2&size=3")

    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 2
    assert data["size"] == 3
    assert len(data["data"]) == 3


@pytest.mark.serial
@pytest.mark.api
def test_get_transactions_max_limit(client, sample_transactions, session):
    """Test transactions retrieval with pagination exceeding max limit"""
    max_page = settings.MAX_TRANSACTION // 25 + 1
    response = client.get(f"/v1/explorer/transactions?page={max_page}&size=25")

    assert response.status_code == 400
    assert str(settings.MAX_TRANSACTION) in response.json()["detail"]


@pytest.mark.serial
@pytest.mark.api
def test_get_transactions_response_structure(client, sample_transactions):
    """Test the structure of transaction response data"""
    response = client.get("/v1/explorer/transactions")

    assert response.status_code == 200
    data = response.json()

    # Check required response fields
    required_response_fields = {"data", "total", "max_display", "page", "size"}
    assert all(field in data for field in required_response_fields)

    # Check transaction data structure
    first_tx = data["data"][0]
    required_tx_fields = {
        "hash",
        "block_number",
        "block_timestamp",
        "transaction_index",
        "from_address",
        "from_addr",
        "to_address",
        "to_addr",
        "method_id",
        "receipt_status",
        "transaction_fee",
        "transaction_fee_usd",
        "value",
        "value_usd",
    }
    assert all(field in first_tx for field in required_tx_fields)
    assert first_tx["hash"].startswith("0x")
    assert isinstance(first_tx["block_number"], int)
    assert isinstance(first_tx["value"], str)


@pytest.mark.serial
@pytest.mark.api
def test_get_transaction_token_transfers_success(
    client, sample_addresses, erc20_token_transfers, erc721_token_transfers, erc1155_token_transfers, session
):
    """Test successful retrieval of token transfers for a transaction"""
    # Test with a transaction that has ERC20 transfers
    tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    response = client.get(f"/v1/explorer/transaction/{tx_hash}/token_transfers")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0

    # Verify transfer data structure
    first_transfer = data["data"][0]
    assert first_transfer["transaction_hash"].startswith("0x")
    assert isinstance(first_transfer["log_index"], int)
    assert first_transfer["from_address"].startswith("0x")
    assert first_transfer["to_address"].startswith("0x")
    assert "from_addr" in first_transfer
    assert "to_addr" in first_transfer
    assert first_transfer["token_info"]["type"] == "ERC20"

    # Test with a transaction that has ERC721 transfers
    tx_hash = "0x3234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    response = client.get(f"/v1/explorer/transaction/{tx_hash}/token_transfers")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert data["data"][0]["token_type"] == "ERC721"
    assert isinstance(data["data"][0]["token_id"], str)


@pytest.mark.serial
@pytest.mark.api
def test_get_transaction_token_transfers_empty(client):
    """Test token transfers for transaction with no transfers"""
    tx_hash = "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    response = client.get(f"/v1/explorer/transaction/{tx_hash}/token_transfers")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["data"]) == 0


@pytest.mark.serial
@pytest.mark.api
def test_get_transaction_token_transfers_invalid_hash(client):
    """Test token transfers with invalid transaction hash"""
    # Test with invalid hex
    response = client.get("/v1/explorer/transaction/invalid_hash/token_transfers")

    assert response.status_code == 422

    # Test with wrong length
    response = client.get("/v1/explorer/transaction/0x123/token_transfers")
    assert response.status_code == 422


@pytest.mark.serial
@pytest.mark.api
def test_get_transaction_token_transfers_response_structure(client, erc20_token_transfers, session):
    """Test the structure of token transfers response data"""
    tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    response = client.get(f"/v1/explorer/transaction/{tx_hash}/token_transfers")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "total" in data
    assert "data" in data
    assert isinstance(data["total"], int)
    assert isinstance(data["data"], list)

    # If we have transfers, check their structure
    if data["data"]:
        transfer = data["data"][0]
        required_fields = {
            "transaction_hash",
            "log_index",
            "from_address",
            "to_address",
            "token_id",
            "value",
            "token_type",
            "token_address",
            "from_addr",
            "to_addr",
        }
        assert all(field in transfer for field in required_fields)

        # Check field types
        assert transfer["transaction_hash"].startswith("0x")
        assert isinstance(transfer["log_index"], int)
        assert transfer["from_address"].startswith("0x")
        assert transfer["to_address"].startswith("0x")
        assert isinstance(transfer["token_type"], str)


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
