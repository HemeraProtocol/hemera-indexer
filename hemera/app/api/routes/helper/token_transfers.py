from datetime import datetime
from typing import Any, List, Literal, Optional, Union

from pydantic import BaseModel
from sqlmodel import Session, desc, func, or_, select

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


class TokenTransferAbbr(BaseModel):
    """Standardized response model for token_transfer"""

    transaction_hash: Optional[str] = None
    log_index: Optional[int] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    token_id: Optional[str] = None
    value: Optional[int] = 0
    token_type: Optional[str] = None
    token_address: Optional[str] = None
    block_number: Optional[int] = None
    block_timestamp: Optional[datetime] = None

    @staticmethod
    def from_db_model(
        transfer: Union[
            ERC20TokenTransfers,
            ERC721TokenTransfers,
            ERC1155TokenTransfers,
            NftTransfers,
            AddressTokenTransfers,
            AddressNftTransfers,
        ]
    ) -> "TokenTransferAbbr":
        """Convert database model to response model"""
        common_fields = {
            "transaction_hash": bytes_to_hex_str(transfer.transaction_hash),
            "log_index": transfer.log_index,
            "block_number": transfer.block_number,
            "block_hash": transfer.block_hash,
            "block_timestamp": transfer.block_timestamp,
            "token_address": bytes_to_hex_str(transfer.token_address),
        }

        if isinstance(transfer, AddressTokenTransfers) or isinstance(transfer, AddressNftTransfers):
            if isinstance(transfer, AddressTokenTransfers):
                token_type = TokenType.ERC20.value
            elif isinstance(transfer, AddressNftTransfers):
                if transfer.value:
                    token_type = TokenType.ERC1155.value
                else:
                    token_type = TokenType.ERC721.value
            else:
                token_type = None
            is_outgoing = transfer.transfer_type in [
                AddressTokenTransferType.SENDER.value,
                AddressNftTransferType.SENDER.value,
                AddressTokenTransferType.DEPOSITOR.value,
                AddressNftTransferType.BURNER.value,
            ]
            common_fields.update(
                {
                    "token_type": token_type,
                    "from_address": bytes_to_hex_str(transfer.address if is_outgoing else transfer.related_address),
                    "to_address": bytes_to_hex_str(transfer.related_address if is_outgoing else transfer.address),
                    "token_id": (
                        getattr(transfer, "token_id", None) if isinstance(transfer, AddressNftTransfers) else None
                    ),
                    "value": getattr(transfer, "value", None),
                }
            )
        else:
            if isinstance(transfer, ERC20TokenTransfers):
                token_type = TokenType.ERC20.value
            elif isinstance(transfer, ERC721TokenTransfers):
                token_type = TokenType.ERC721.value
            elif isinstance(transfer, ERC1155TokenTransfers):
                token_type = TokenType.ERC1155.value
            else:
                if transfer.value:
                    token_type = TokenType.ERC721.value
                else:
                    token_type = TokenType.ERC1155.value
            common_fields.update(
                {
                    "from_address": bytes_to_hex_str(transfer.from_address),
                    "to_address": bytes_to_hex_str(transfer.to_address),
                    "token_id": getattr(transfer, "token_id", None),
                    "value": getattr(transfer, "value", None),
                    "token_type": token_type,
                }
            )
        if common_fields.get("token_id") is not None:
            common_fields["token_id"] = str(common_fields["token_id"])
        return TokenTransferAbbr(**common_fields)


def _get_erc20_token_transfers_by_hash(session: Session, hash: str) -> List[ERC20TokenTransfers]:
    """Get ERC20 token transfer by transaction hash"""
    hash_bytes = hex_str_to_bytes(hash)
    return session.exec(select(ERC20TokenTransfers).where(ERC20TokenTransfers.transaction_hash == hash_bytes)).all()


def _get_erc721_token_transfers_by_hash(session: Session, hash: str) -> List[ERC721TokenTransfers]:
    """Get ERC721 token transfer by transaction hash"""
    hash_bytes = hex_str_to_bytes(hash)
    return session.exec(select(ERC721TokenTransfers).where(ERC721TokenTransfers.transaction_hash == hash_bytes)).all()


def _get_erc1155_token_transfers_by_hash(session: Session, hash: str) -> List[ERC1155TokenTransfers]:
    """Get ERC1155 token transfer by transaction hash"""
    hash_bytes = hex_str_to_bytes(hash)
    return session.exec(select(ERC1155TokenTransfers).where(ERC1155TokenTransfers.transaction_hash == hash_bytes)).all()


def _get_nft_transfers_by_hash(
    session: Session, hash: str, token_type: Literal["erc721", "erc1155", "all"] = "all"
) -> List[NftTransfers]:
    """Get NFT transfer by transaction hash from unified NFT table"""
    hash_bytes = hex_str_to_bytes(hash)
    statement = select(NftTransfers).where(NftTransfers.transaction_hash == hash_bytes)

    if token_type == "erc721":
        statement = statement.where(NftTransfers.value == None)
    elif token_type == "erc1155":
        statement = statement.where(NftTransfers.value != None)

    return session.exec(statement).all()


def get_token_transfers_by_hash(
    session: Session,
    hash: str,
    token_type: Literal["ERC20", "ERC721", "ERC1155", "ALL"] = "ALL",
    use_unified_table: bool = False,
) -> List[TokenTransferAbbr]:
    """
    Get token transfer by transaction hash

    Args:
        session: SQLModel session
        hash: Transaction hash in hex string format
        token_type: Type of token transfer to query
        use_unified_table: Whether to use unified NFT table for NFT transfers
    """
    # For NFT transfers, use unified table if specified
    transfers = []
    if token_type in ["ERC20", "ERC721", "ALL"] and use_unified_table:
        transfers.extend(_get_nft_transfers_by_hash(session, hash, token_type))
        if token_type == "ALL":
            transfers.extend(_get_erc20_token_transfers_by_hash(session, hash))
    else:
        if token_type == "ERC20":
            transfers.extend(_get_erc20_token_transfers_by_hash(session, hash))
        elif token_type == "ERC721":
            transfers.extend(_get_erc721_token_transfers_by_hash(session, hash))
        elif token_type == "ERC1155":
            transfers.extend(_get_erc1155_token_transfers_by_hash(session, hash))
        else:
            transfers.extend(_get_erc20_token_transfers_by_hash(session, hash))
            transfers.extend(_get_erc721_token_transfers_by_hash(session, hash))
            transfers.extend(_get_erc1155_token_transfers_by_hash(session, hash))

    return [TokenTransferAbbr.from_db_model(transfer) for transfer in transfers if transfer]


def _get_erc20_transfers_by_address_native(
    session: Session,
    address: Union[str, bytes],
    direction: Optional[Literal["from", "to", "both"]] = "both",
    token_address: Optional[Union[str, bytes]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[ERC20TokenTransfers]:
    """Get ERC20 transfers by address using native table"""
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    if isinstance(token_address, str):
        token_address = hex_str_to_bytes(token_address)

    statement = select(ERC20TokenTransfers)

    if direction == "from":
        statement = statement.where(ERC20TokenTransfers.from_address == address)
    elif direction == "to":
        statement = statement.where(ERC20TokenTransfers.to_address == address)
    else:  # both
        statement = statement.where(
            or_(ERC20TokenTransfers.from_address == address, ERC20TokenTransfers.to_address == address)
        )

    if token_address:
        statement = statement.where(ERC20TokenTransfers.token_address == token_address)

    statement = statement.order_by(
        desc(ERC20TokenTransfers.block_timestamp),
        desc(ERC20TokenTransfers.block_number),
        desc(ERC20TokenTransfers.log_index),
    )

    if limit:
        statement = statement.limit(limit)
    if offset:
        statement = statement.offset(offset)

    return session.exec(statement).all()


def _get_erc721_transfers_by_address_native(
    session: Session,
    address: Union[str, bytes],
    direction: Optional[Literal["from", "to", "both"]] = "both",
    token_address: Optional[Union[str, bytes]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[ERC721TokenTransfers]:
    """Get ERC721 transfers by address using native table"""
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    if isinstance(token_address, str):
        token_address = hex_str_to_bytes(token_address)

    statement = select(ERC721TokenTransfers)

    if direction == "from":
        statement = statement.where(ERC721TokenTransfers.from_address == address)
    elif direction == "to":
        statement = statement.where(ERC721TokenTransfers.to_address == address)
    else:  # both
        statement = statement.where(
            or_(ERC721TokenTransfers.from_address == address, ERC721TokenTransfers.to_address == address)
        )

    if token_address:
        statement = statement.where(ERC721TokenTransfers.token_address == token_address)

    statement = statement.order_by(ERC721TokenTransfers.block_timestamp.desc())

    if limit:
        statement = statement.limit(limit)
    if offset:
        statement = statement.offset(offset)

    return session.exec(statement).all()


def _get_erc1155_transfers_by_address_native(
    session: Session,
    address: Union[str, bytes],
    direction: Optional[Literal["from", "to", "both"]] = "both",
    token_address: Optional[Union[str, bytes]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[ERC1155TokenTransfers]:
    """Get ERC1155 transfers by address using native table"""
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    if isinstance(token_address, str):
        token_address = hex_str_to_bytes(token_address)

    statement = select(ERC1155TokenTransfers)

    if direction == "from":
        statement = statement.where(ERC1155TokenTransfers.from_address == address)
    elif direction == "to":
        statement = statement.where(ERC1155TokenTransfers.to_address == address)
    else:  # both
        statement = statement.where(
            or_(ERC1155TokenTransfers.from_address == address, ERC1155TokenTransfers.to_address == address)
        )

    if token_address:
        statement = statement.where(ERC1155TokenTransfers.token_address == token_address)

    statement = statement.order_by(ERC1155TokenTransfers.block_timestamp.desc())

    if limit:
        statement = statement.limit(limit)
    if offset:
        statement = statement.offset(offset)

    return session.exec(statement).all()


def get_nft_transfers_by_address_native(
    session: Session,
    address: Union[str, bytes],
    direction: Optional[Literal["from", "to", "both"]] = "both",
    token_type: Literal["erc721", "erc1155", "all"] = "all",
    token_address: Optional[Union[str, bytes]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[NftTransfers]:
    """Get NFT transfers by address from unified NFT table"""
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    if isinstance(token_address, str):
        token_address = hex_str_to_bytes(token_address)

    statement = select(NftTransfers)

    if direction == "from":
        statement = statement.where(NftTransfers.from_address == address)
    elif direction == "to":
        statement = statement.where(NftTransfers.to_address == address)
    else:  # both
        statement = statement.where(or_(NftTransfers.from_address == address, NftTransfers.to_address == address))

    if token_type == "erc721":
        statement = statement.where(NftTransfers.value == None)
    elif token_type == "erc1155":
        statement = statement.where(NftTransfers.value != None)

    if token_address:
        statement = statement.where(NftTransfers.token_address == token_address)

    statement = statement.order_by(NftTransfers.block_timestamp.desc())

    if limit:
        statement = statement.limit(limit)
    if offset:
        statement = statement.offset(offset)

    return session.exec(statement).all()


def _get_erc20_transfers_by_address_index(
    session: Session,
    address: Union[str, bytes],
    token_address: Optional[Union[str, bytes]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[AddressTokenTransfers]:
    """Get ERC20 transfers by address using address index table"""
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    if isinstance(token_address, str):
        token_address = hex_str_to_bytes(token_address)

    statement = select(AddressTokenTransfers).where(
        AddressTokenTransfers.address == address,
    )

    if token_address:
        statement = statement.where(AddressTokenTransfers.token_address == token_address)

    statement = statement.order_by(AddressTokenTransfers.block_timestamp.desc())

    if limit:
        statement = statement.limit(limit)
    if offset:
        statement = statement.offset(offset)

    return session.exec(statement).all()


def _get_erc721_transfers_by_address_index(
    session: Session,
    address: Union[str, bytes],
    token_address: Optional[Union[str, bytes]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[AddressNftTransfers]:
    """Get ERC721 transfers by address using address index table"""
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    if isinstance(token_address, str):
        token_address = hex_str_to_bytes(token_address)

    statement = select(AddressNftTransfers).where(
        AddressNftTransfers.address == address and AddressNftTransfers.value == None
    )

    if token_address:
        statement = statement.where(AddressNftTransfers.token_address == token_address)

    statement = statement.order_by(
        desc(AddressNftTransfers.block_timestamp),
        desc(AddressNftTransfers.block_number),
        desc(AddressNftTransfers.log_index),
    )

    if limit:
        statement = statement.limit(limit)
    if offset:
        statement = statement.offset(offset)

    return session.exec(statement).all()


def _get_erc1155_transfers_by_address_index(
    session: Session,
    address: Union[str, bytes],
    token_address: Optional[Union[str, bytes]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[AddressNftTransfers]:
    """Get ERC1155 transfers by address using address index table"""
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    if isinstance(token_address, str):
        token_address = hex_str_to_bytes(token_address)

    statement = select(AddressNftTransfers).where(
        AddressNftTransfers.address == address and AddressNftTransfers.value != None
    )

    if token_address:
        statement = statement.where(AddressNftTransfers.token_address == token_address)

    statement = statement.order_by(AddressNftTransfers.block_timestamp.desc())

    if limit:
        statement = statement.limit(limit)
    if offset:
        statement = statement.offset(offset)

    return session.exec(statement).all()


def get_token_transfers_by_address(
    session: Session,
    address: Union[str, bytes],
    token_type: Literal["ERC20", "ERC721", "ERC1155", "ALL"] = "ALL",
    direction: Optional[Literal["from", "to", "both"]] = "both",
    token_address: Optional[Union[str, bytes]] = None,
    use_address_index: bool = False,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[TokenTransferAbbr]:
    """
    Get token transfers by address with flexible options for querying

    Args:
        session: SQLModel session
        address: Address to query
        token_type: Type of token transfers to query
        direction: Filter direction (only used for native table queries)
        token_address: Optional token address to filter by
        use_address_index: Whether to use address index tables
        limit: Max number of records to return
        offset: Number of records to skip
    """
    transfers = []
    if use_address_index:
        # Use address index tables
        if token_type == "ERC20":
            transfers.extend(_get_erc20_transfers_by_address_index(session, address, token_address, limit, offset))
        elif token_type == "ERC721":
            transfers.extend(_get_erc721_transfers_by_address_index(session, address, token_address, limit, offset))
        elif token_type == "ERC1155":
            transfers.extend(_get_erc1155_transfers_by_address_index(session, address, token_address, limit, offset))
        else:  # all
            transfers = []
            transfers.extend(_get_erc20_transfers_by_address_index(session, address, token_address, limit, offset))
            transfers.extend(_get_erc721_transfers_by_address_index(session, address, token_address, limit, offset))
            transfers.extend(_get_erc1155_transfers_by_address_index(session, address, token_address, limit, offset))
            transfers.extend(transfers)
    else:
        # Use native tables
        if token_type == "ERC20":
            transfers.extend(
                _get_erc20_transfers_by_address_native(session, address, direction, token_address, limit, offset)
            )
        elif token_type == "ERC721":
            transfers.extend(
                _get_erc721_transfers_by_address_native(session, address, direction, token_address, limit, offset)
            )
        elif token_type == "ERC1155":
            transfers.extend(
                _get_erc1155_transfers_by_address_native(session, address, direction, token_address, limit, offset)
            )
        else:  # all
            transfers.extend(
                _get_erc20_transfers_by_address_native(session, address, direction, token_address, limit, offset)
            )
            transfers.extend(
                _get_erc721_transfers_by_address_native(session, address, direction, token_address, limit, offset)
            )
            transfers.extend(
                _get_erc1155_transfers_by_address_native(session, address, direction, token_address, limit, offset)
            )
    return [TokenTransferAbbr.from_db_model(transfer) for transfer in transfers if transfer]


def _get_erc20_token_transfers_by_condition(
    session: Session,
    filter_condition: Optional[Any] = None,
    limit: Optional[int] = 25,
    offset: Optional[int] = 0,
) -> List[ERC20TokenTransfers]:
    """Get ERC20 token transfers by condition"""
    statement = select(ERC20TokenTransfers)
    if filter_condition:
        statement = statement.where(filter_condition)
    statement = statement.order_by(desc(ERC20TokenTransfers.block_number), desc(ERC20TokenTransfers.log_index))
    if limit:
        statement = statement.limit(limit)
    if offset:
        statement = statement.offset(offset)
    return session.exec(statement).all()


def _get_erc721_token_transfers_by_condition(
    session: Session,
    filter_condition: Optional[Any] = None,
    limit: Optional[int] = 25,
    offset: Optional[int] = 0,
) -> List[ERC721TokenTransfers]:
    """Get ERC721 token transfers by condition"""
    statement = select(ERC721TokenTransfers)
    if filter_condition:
        statement = statement.where(filter_condition)
    statement = statement.order_by(desc(ERC721TokenTransfers.block_number), desc(ERC721TokenTransfers.log_index))
    if limit:
        statement = statement.limit(limit)
    if offset:
        statement = statement.offset(offset)
    return session.exec(statement).all()


def _get_erc1155_token_transfers_by_condition(
    session: Session,
    filter_condition: Optional[Any] = None,
    limit: Optional[int] = 25,
    offset: Optional[int] = 0,
) -> List[ERC1155TokenTransfers]:
    """Get ERC1155 token transfers by condition"""
    statement = select(ERC1155TokenTransfers)
    if filter_condition:
        statement = statement.where(filter_condition)
    statement = statement.order_by(desc(ERC1155TokenTransfers.block_number), desc(ERC1155TokenTransfers.log_index))
    if limit:
        statement = statement.limit(limit)
    if offset:
        statement = statement.offset(offset)
    return session.exec(statement).all()


def _get_erc20_token_transfers_count(
    session: Session,
    filter_condition: Optional[Any] = None,
) -> int:
    """Get the total count of ERC1155 token transfers by condition"""
    statement = select(func.count()).select_from(ERC20TokenTransfers)
    if filter_condition:
        statement = statement.where(filter_condition)
    count = session.exec(statement).one()
    return count


def _get_erc721_token_transfers_count(
    session: Session,
    filter_condition: Optional[Any] = None,
) -> int:
    """Get the total count of ERC1155 token transfers by condition"""
    statement = select(func.count()).select_from(ERC721TokenTransfers)
    if filter_condition:
        statement = statement.where(filter_condition)
    count = session.exec(statement).one()
    return count


def _get_erc1155_token_transfers_count(
    session: Session,
    filter_condition: Optional[Any] = None,
) -> int:
    """Get the total count of ERC1155 token transfers by condition"""
    statement = select(func.count()).select_from(ERC1155TokenTransfers)
    if filter_condition:
        statement = statement.where(filter_condition)
    count = session.exec(statement).one()
    return count


def get_token_transfers_by_token_address(
    session: Session,
    token_address: Union[str, bytes],
    token_type: Literal["ERC20", "ERC721", "ERC1155"] = "ERC20",
    limit: int = 25,
    offset: int = 0,
) -> (int, List[TokenTransferAbbr]):
    """
    Get token transfers by token address

    Args:
        session: SQLModel session
        token_addresses: List of token addresses
        token_type: Type of token transfers to query
        limit: Max number of records to return
        offset: Number of records to skip
    """
    if isinstance(token_address, str):
        token_address = hex_str_to_bytes(token_address)
    transfers = []
    if token_type == "ERC20":
        filter_condition = ERC20TokenTransfers.token_address == token_address
    elif token_type == "ERC721":
        filter_condition = ERC20TokenTransfers.token_address == token_address
    elif token_type == "ERC1155":
        filter_condition = ERC20TokenTransfers.token_address == token_address
    else:
        filter_condition = None
    return get_token_transfers(session, filter_condition, token_type, limit, offset)


def get_token_transfers(
    session: Session,
    filter_condition: Optional[Any] = None,
    token_type: Literal["ERC20", "ERC721", "ERC1155"] = "ERC20",
    limit: int = 25,
    offset: int = 0,
) -> (int, List[TokenTransferAbbr]):
    """
    Get token transfers with pagination

    Args:
        session: SQLModel session
        filter_condition: Optional filter condition
        limit: Number of records to return
        offset: Number of records to skip
    """
    transfers = []
    total_count = 0

    if token_type == "ERC20":
        transfers = _get_erc20_token_transfers_by_condition(session, filter_condition, limit=limit, offset=offset)
        total_count = _get_erc20_token_transfers_count(session, filter_condition)
    elif token_type == "ERC721":
        transfers = _get_erc721_token_transfers_by_condition(session, filter_condition, limit=limit, offset=offset)
        total_count = _get_erc721_token_transfers_count(session, filter_condition)
    elif token_type == "ERC1155":
        transfers = _get_erc1155_token_transfers_by_condition(session, filter_condition, limit=limit, offset=offset)
        total_count = _get_erc1155_token_transfers_count(session, filter_condition)

    return total_count, [TokenTransferAbbr.from_db_model(transfer) for transfer in transfers if transfer]
