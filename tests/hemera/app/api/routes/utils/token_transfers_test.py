from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from hemera.app.api.routes.helper.token_transfers import (
    TokenTransferAbbr,
    _get_erc20_token_transfers_by_hash,
    _get_erc20_transfers_by_address_index,
    _get_erc20_transfers_by_address_native,
    _get_erc721_token_transfers_by_hash,
    _get_erc721_transfers_by_address_index,
    _get_erc721_transfers_by_address_native,
    _get_erc1155_token_transfers_by_hash,
    _get_erc1155_transfers_by_address_index,
    _get_erc1155_transfers_by_address_native,
    _get_nft_transfers_by_hash,
    get_nft_transfers_by_address_native,
    get_token_transfers_by_address,
    get_token_transfers_by_hash,
)
from hemera.common.enumeration.token_type import TokenType
from hemera.common.enumeration.txn_type import AddressNftTransferType, AddressTokenTransferType
from hemera.common.models.address.address_nft_transfers import AddressNftTransfers
from hemera.common.models.address.address_token_transfers import AddressTokenTransfers
from hemera.common.models.token_transfers import (
    ERC20TokenTransfers,
    ERC721TokenTransfers,
    ERC1155TokenTransfers,
    NftTransfers,
)
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes


@pytest.fixture
def sample_addresses():
    return {
        "sender": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "receiver": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "token": "0xcccccccccccccccccccccccccccccccccccccccc",
    }


@pytest.fixture
def erc20_token_transfers(session, sample_addresses):
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


def test_get_erc20_token_transfer_by_hash(session, erc20_token_transfers):
    """Test querying ERC20 transfer by hash"""
    # Test existing transfer
    hash_str = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    transfers = _get_erc20_token_transfers_by_hash(session, hash_str)
    assert len(transfers) == 1
    transfer = transfers[0]
    assert transfer.block_number == 21436149
    assert transfer.log_index == 0
    assert transfer.value == Decimal("1000000000000000000")

    # Test non-existent hash
    transfers = _get_erc20_token_transfers_by_hash(session, "0xffff")
    assert len(transfers) == 0

    # Test invalid hash
    with pytest.raises(ValueError):
        _get_erc20_token_transfers_by_hash(session, "invalid_hash")


def test_get_erc721_token_transfer_by_hash(session, erc721_token_transfers):
    """Test querying ERC721 transfer by hash"""
    # Test existing transfer
    hash_str = "0x3234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    transfers = _get_erc721_token_transfers_by_hash(session, hash_str)
    assert len(transfers) == 1
    transfer = transfers[0]
    assert transfer.block_number == 21436149
    assert transfer.log_index == 0
    assert transfer.token_id == Decimal("1")

    # Test non-existent hash
    transfers = _get_erc721_token_transfers_by_hash(session, "0xffff")
    assert len(transfers) == 0

    # Test invalid hash
    with pytest.raises(ValueError):
        _get_erc721_token_transfers_by_hash(session, "invalid_hash")


def test_get_erc1155_token_transfer_by_hash(session, erc1155_token_transfers):
    """Test querying ERC1155 transfer by hash"""
    # Test existing transfer
    hash_str = "0x5234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    transfers = _get_erc1155_token_transfers_by_hash(session, hash_str)
    assert len(transfers) == 1
    transfer = transfers[0]
    assert transfer.block_number == 21436149
    assert transfer.log_index == 0
    assert transfer.token_id == Decimal("1")
    assert transfer.value == Decimal("5")

    # Test non-existent hash
    transfers = _get_erc1155_token_transfers_by_hash(session, "0xffff")
    assert len(transfers) == 0

    # Test invalid hash
    with pytest.raises(ValueError):
        _get_erc1155_token_transfers_by_hash(session, "invalid_hash")


def test_get_nft_transfer_by_hash(session, nft_transfers):
    """Test querying NFT transfer by hash from unified table"""
    # Test existing ERC721 transfer
    hash_str = "0x7234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    transfers = _get_nft_transfers_by_hash(session, hash_str, token_type="erc721")
    assert len(transfers) == 1
    transfer = transfers[0]
    assert transfer.block_number == 21436149
    assert transfer.value is None
    assert transfer.token_id == Decimal("1")

    # Test existing ERC1155 transfer
    hash_str = "0x8234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    transfers = _get_nft_transfers_by_hash(session, hash_str, token_type="erc1155")
    assert len(transfers) == 1
    transfer = transfers[0]
    assert transfer.value == Decimal("5")
    assert transfer.token_id == Decimal("2")

    # Test non-existent hash
    transfers = _get_nft_transfers_by_hash(session, "0xffff")
    assert len(transfers) == 0

    # Test invalid hash
    with pytest.raises(ValueError):
        _get_nft_transfers_by_hash(session, "invalid_hash")


def test_multiple_transfers_same_hash(session, sample_addresses):
    """Test handling of multiple transfers in the same transaction"""
    now = datetime.utcnow()
    tx_hash = hex_str_to_bytes("0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
    block_hash = hex_str_to_bytes("0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff")

    # Create multiple ERC1155 transfers with same hash but different token_ids
    transfers = [
        ERC1155TokenTransfers(
            transaction_hash=tx_hash,
            block_number=21436149,
            block_timestamp=now,
            from_address=hex_str_to_bytes(sample_addresses["sender"]),
            to_address=hex_str_to_bytes(sample_addresses["receiver"]),
            token_address=hex_str_to_bytes(sample_addresses["token"]),
            token_id=Decimal(str(i)),
            value=Decimal("1"),
            log_index=i,
            block_hash=block_hash,
        )
        for i in range(3)
    ]

    for transfer in transfers:
        session.add(transfer)
    session.commit()

    # Query by hash should return all transfers
    results = _get_erc1155_token_transfers_by_hash(session, bytes_to_hex_str(tx_hash))
    assert len(results) == 3
    assert sorted([t.token_id for t in results]) == [Decimal("0"), Decimal("1"), Decimal("2")]

    # Query by address should return all transfers
    results = _get_erc1155_transfers_by_address_native(session, sample_addresses["sender"], direction="from")
    assert len([t for t in results if t.transaction_hash == tx_hash]) == 3


def test_response_model_conversion(session, erc20_token_transfers, address_token_transfers):
    """Test conversion of different models to TokenTransfer response model"""
    # Test ERC20 native table conversion
    transfers = _get_erc20_token_transfers_by_hash(
        session, "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    )
    assert len(transfers) > 0
    response = TokenTransferAbbr.from_db_model(transfers[0])
    assert isinstance(response, TokenTransferAbbr)
    assert response.token_type == TokenType.ERC20.value
    assert response.value is not None
    assert response.token_id is None

    # Test address index table conversion
    addr_transfers = _get_erc20_transfers_by_address_index(
        session, bytes_to_hex_str(address_token_transfers[0].address)
    )
    assert len(addr_transfers) > 0
    response = TokenTransferAbbr.from_db_model(addr_transfers[0])
    assert isinstance(response, TokenTransferAbbr)
    assert response.token_type == TokenType.ERC20.value
    assert response.from_address is not None
    assert response.to_address is not None


def test_get_token_transfer_by_hash_using_unified_table(session, nft_transfers, erc20_token_transfers):
    """Test querying token transfers using unified table"""
    # Test ERC20 transfer included when token_type is "all"
    hash_str = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    transfers = get_token_transfers_by_hash(session, hash_str, token_type="ALL", use_unified_table=True)
    assert len(transfers) == 1
    transfer = transfers[0]
    assert transfer.token_type == TokenType.ERC20.value
    assert transfer.value == 1000000000000000000

    # Test NFT transfer filtered by type
    hash_str = "0x7234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    transfers = get_token_transfers_by_hash(session, hash_str, token_type="ERC721", use_unified_table=True)
    assert len(transfers) == 1
    transfer = transfers[0]
    assert transfer.token_id == "1"
    assert transfer.value is None


def test_get_token_transfer_by_hash_using_separate_tables(
    session, erc20_token_transfers, erc721_token_transfers, erc1155_token_transfers
):
    """Test querying token transfers using separate tables"""
    # Test ERC20 transfer
    hash_str = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    transfers = get_token_transfers_by_hash(session, hash_str, token_type="ERC20", use_unified_table=False)
    assert len(transfers) == 1
    transfer = transfers[0]
    assert transfer.token_type == TokenType.ERC20.value
    assert transfer.value == 1000000000000000000

    # Test ERC721 transfer
    hash_str = "0x3234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    transfers = get_token_transfers_by_hash(session, hash_str, token_type="ERC721", use_unified_table=False)
    assert len(transfers) == 1
    transfer = transfers[0]
    assert transfer.token_type == TokenType.ERC721.value
    assert transfer.token_id == "1"

    # Test all types
    hash_str = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    transfers = get_token_transfers_by_hash(session, hash_str, token_type="ALL", use_unified_table=False)
    assert len(transfers) == 1  # Should only find the ERC20 transfer for this hash
    assert transfers[0].token_type == TokenType.ERC20.value


def test_get_erc20_transfers_by_address_native(session, erc20_token_transfers, sample_addresses):
    """Test querying ERC20 transfers by address using native table"""
    # Test from direction
    transfers = _get_erc20_transfers_by_address_native(session, sample_addresses["sender"], direction="from")
    assert len(transfers) == 2
    assert all(tx.from_address == hex_str_to_bytes(sample_addresses["sender"]) for tx in transfers)

    # Test to direction
    transfers = _get_erc20_transfers_by_address_native(session, sample_addresses["receiver"], direction="to")
    assert len(transfers) == 2
    assert all(tx.to_address == hex_str_to_bytes(sample_addresses["receiver"]) for tx in transfers)

    # Test both direction
    transfers = _get_erc20_transfers_by_address_native(session, sample_addresses["sender"], direction="both")
    assert len(transfers) == 2  # All transfers where address is either sender or receiver

    # Test with token_address filter
    transfers = _get_erc20_transfers_by_address_native(
        session, sample_addresses["sender"], token_address=sample_addresses["token"]
    )
    assert len(transfers) > 0
    assert all(tx.token_address == hex_str_to_bytes(sample_addresses["token"]) for tx in transfers)

    # Test with limit and offset
    transfers = _get_erc20_transfers_by_address_native(session, sample_addresses["sender"], limit=1, offset=1)
    assert len(transfers) == 1


def test_get_erc721_transfers_by_address_native(session, erc721_token_transfers, sample_addresses):
    """Test querying ERC721 transfers by address using native table"""
    # Test from direction
    transfers = _get_erc721_transfers_by_address_native(session, sample_addresses["sender"], direction="from")
    assert len(transfers) == 1
    assert all(tx.from_address == hex_str_to_bytes(sample_addresses["sender"]) for tx in transfers)
    assert all(tx.token_id is not None for tx in transfers)

    # Test to direction
    transfers = _get_erc721_transfers_by_address_native(session, sample_addresses["receiver"], direction="to")
    assert len(transfers) == 1
    assert all(tx.to_address == hex_str_to_bytes(sample_addresses["receiver"]) for tx in transfers)

    # Test both direction
    transfers = _get_erc721_transfers_by_address_native(session, sample_addresses["receiver"], direction="both")
    assert len(transfers) == 2

    # Test with token_address filter
    transfers = _get_erc721_transfers_by_address_native(
        session, sample_addresses["sender"], token_address=sample_addresses["token"]
    )
    assert len(transfers) > 0
    assert all(tx.token_address == hex_str_to_bytes(sample_addresses["token"]) for tx in transfers)


def test_get_erc1155_transfers_by_address_native(session, erc1155_token_transfers, sample_addresses):
    """Test querying ERC1155 transfers by address using native table"""
    # Test from direction
    transfers = _get_erc1155_transfers_by_address_native(session, sample_addresses["sender"], direction="from")
    assert len(transfers) == 2
    assert all(tx.from_address == hex_str_to_bytes(sample_addresses["sender"]) for tx in transfers)
    assert all(tx.value is not None for tx in transfers)

    # Test to direction
    transfers = _get_erc1155_transfers_by_address_native(session, sample_addresses["receiver"], direction="to")
    assert len(transfers) == 2
    assert all(tx.to_address == hex_str_to_bytes(sample_addresses["receiver"]) for tx in transfers)

    # Test with specific token_id
    first_transfer = erc1155_token_transfers[0]
    transfers = _get_erc1155_transfers_by_address_native(
        session, sample_addresses["sender"], token_address=sample_addresses["token"]
    )
    assert len(transfers) > 0
    matching_transfer = next(tx for tx in transfers if tx.token_id == first_transfer.token_id)
    assert matching_transfer.value == first_transfer.value


def test_get_nft_transfers_by_address_native(session, nft_transfers, sample_addresses):
    """Test querying NFT transfers by address from unified table"""
    # Test ERC721 transfers
    transfers = get_nft_transfers_by_address_native(session, sample_addresses["sender"], token_type="erc721")
    assert len(transfers) >= 1
    assert all(tx.value is None for tx in transfers)  # ERC721 has no value

    # Test ERC1155 transfers
    transfers = get_nft_transfers_by_address_native(session, sample_addresses["sender"], token_type="erc1155")
    assert len(transfers) >= 1
    assert all(tx.value is not None for tx in transfers)  # ERC1155 has value

    # Test all NFT transfers
    transfers = get_nft_transfers_by_address_native(session, sample_addresses["sender"], token_type="all")
    assert len(transfers) >= 2  # Should include both ERC721 and ERC1155


def test_get_erc20_transfers_by_address_index(session, address_token_transfers, sample_addresses):
    """Test querying ERC20 transfers by address using address index"""
    transfers = _get_erc20_transfers_by_address_index(session, sample_addresses["sender"])
    assert len(transfers) == 1
    assert transfers[0].address == hex_str_to_bytes(sample_addresses["sender"])
    assert transfers[0].transfer_type == AddressTokenTransferType.SENDER.value

    # Test with token address filter
    transfers = _get_erc20_transfers_by_address_index(
        session, sample_addresses["sender"], token_address=sample_addresses["token"]
    )
    assert len(transfers) == 1
    assert all(tx.token_address == hex_str_to_bytes(sample_addresses["token"]) for tx in transfers)


def test_get_erc721_transfers_by_address_index(session, address_nft_transfers, sample_addresses):
    """Test querying ERC721 transfers by address using address index"""
    transfers = _get_erc721_transfers_by_address_index(session, sample_addresses["sender"])
    assert len(transfers) == 1
    assert transfers[0].address == hex_str_to_bytes(sample_addresses["sender"])
    assert transfers[0].value is None  # ERC721 has no value
    assert transfers[0].transfer_type == AddressNftTransferType.SENDER.value


def test_get_erc1155_transfers_by_address_index(session, address_nft_transfers, sample_addresses):
    """Test querying ERC1155 transfers by address using address index"""
    transfers = _get_erc1155_transfers_by_address_index(session, sample_addresses["receiver"])
    assert len(transfers) == 1
    assert transfers[0].address == hex_str_to_bytes(sample_addresses["receiver"])
    assert transfers[0].value is not None  # ERC1155 has value
    assert transfers[0].transfer_type == AddressNftTransferType.RECEIVER.value


def test_get_token_transfers_by_address_using_address_index(
    session, address_token_transfers, address_nft_transfers, sample_addresses
):
    """Test unified query for token transfers using address index"""
    # Test ERC20 transfers
    transfers = get_token_transfers_by_address(
        session, sample_addresses["sender"], token_type="ERC20", use_address_index=True
    )
    assert len(transfers) == 1
    assert isinstance(transfers[0], TokenTransferAbbr)

    # Test ERC721 transfers
    transfers = get_token_transfers_by_address(
        session, sample_addresses["sender"], token_type="ERC721", use_address_index=True
    )
    assert len(transfers) == 1
    assert isinstance(transfers[0], TokenTransferAbbr)
    assert transfers[0].value is None

    # Test ERC1155 transfers
    transfers = get_token_transfers_by_address(
        session, sample_addresses["receiver"], token_type="ERC1155", use_address_index=True
    )
    assert len(transfers) == 1
    assert isinstance(transfers[0], TokenTransferAbbr)
    assert transfers[0].value is not None

    # Test all token types
    transfers = get_token_transfers_by_address(
        session, sample_addresses["sender"], token_type="ALL", use_address_index=True
    )
    assert len(transfers) == 6  # Should include both ERC20 and NFTs


def test_get_token_transfers_by_address_using_native_tables(
    session, erc20_token_transfers, erc721_token_transfers, erc1155_token_transfers, sample_addresses
):
    """Test unified query for token transfers using native tables"""
    # Test filtering by token type
    for token_type in ["ERC20", "ERC721", "ERC1155"]:
        transfers = get_token_transfers_by_address(
            session, sample_addresses["sender"], token_type=token_type, use_address_index=False
        )
        assert len(transfers) > 0
        if token_type == "erc20":
            assert isinstance(transfers[0], TokenTransferAbbr)
        elif token_type == "erc721":
            assert isinstance(transfers[0], TokenTransferAbbr)
        else:
            assert isinstance(transfers[0], TokenTransferAbbr)

    # Test direction filtering
    transfers = get_token_transfers_by_address(
        session, sample_addresses["sender"], token_type="all", direction="from", use_address_index=False
    )
    assert all(tx.from_address == sample_addresses["sender"] for tx in transfers)

    # Test with token address filter
    transfers = get_token_transfers_by_address(
        session,
        sample_addresses["sender"],
        token_type="all",
        token_address=sample_addresses["token"],
        use_address_index=False,
    )
    assert all(tx.token_address == sample_addresses["token"] for tx in transfers)

    # Test pagination
    all_transfers = get_token_transfers_by_address(
        session, sample_addresses["sender"], token_type="all", use_address_index=False
    )
    paginated_transfers = get_token_transfers_by_address(
        session, sample_addresses["sender"], token_type="all", use_address_index=False, limit=1
    )
    assert len(paginated_transfers) == 3
    assert paginated_transfers[0].transaction_hash == all_transfers[0].transaction_hash


def test_empty_result_handling(session):
    """Test handling of queries that return no results"""
    # Use a random valid address that shouldn't exist in test data
    non_existent_address = "0x1111111111111111111111111111111111111111"

    # Test native table queries
    transfers = _get_erc20_transfers_by_address_native(session, non_existent_address)
    assert isinstance(transfers, list)
    assert len(transfers) == 0

    # Test index table queries
    transfers = _get_erc20_transfers_by_address_index(session, non_existent_address)
    assert isinstance(transfers, list)
    assert len(transfers) == 0

    # Test unified query
    transfers = get_token_transfers_by_address(session, non_existent_address, token_type="all")
    assert isinstance(transfers, list)
    assert len(transfers) == 0


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
