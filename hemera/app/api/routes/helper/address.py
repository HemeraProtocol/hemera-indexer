#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/22
# @Author  ideal93
# @File  address_utils.py
# @Brief

from enum import Enum
from typing import Optional, Union

from sqlmodel import Session, select

from hemera.app.api.routes.helper import ColumnType
from hemera.common.models.address.stats.address_index_stats import AddressIndexStats
from hemera.common.utils.format_utils import hex_str_to_bytes


class TokenTransferType(str, Enum):
    """Token transfer types for address statistics"""

    ERC20 = "erc20"
    ERC721 = "erc721"
    ERC1155 = "erc1155"
    TOKEN_TXNS = "tokentxns"
    TOKEN_TXNS_NFT = "tokentxns-nft"
    TOKEN_TXNS_NFT1155 = "tokentxns-nft1155"


# Mapping from token type to stats column
TOKEN_TYPE_TO_COLUMN = {
    TokenTransferType.TOKEN_TXNS: AddressIndexStats.erc20_transfer_count,
    TokenTransferType.TOKEN_TXNS_NFT: AddressIndexStats.nft_721_transfer_count,
    TokenTransferType.TOKEN_TXNS_NFT1155: AddressIndexStats.nft_1155_transfer_count,
    TokenTransferType.ERC20: AddressIndexStats.erc20_transfer_count,
    TokenTransferType.ERC721: AddressIndexStats.nft_721_transfer_count,
    TokenTransferType.ERC1155: AddressIndexStats.nft_1155_transfer_count,
}


def get_txn_cnt_by_address(session: Session, address: str) -> Optional[int]:
    bytes_address = hex_str_to_bytes(address)
    statement = select(AddressIndexStats.transaction_count).where(AddressIndexStats.address == bytes_address)
    return session.exec(statement).first()


def get_token_transfer_count(
    session: Session, address: str, token_type: Union[str, TokenTransferType], columns: ColumnType = "*"
) -> Optional[int]:
    """Get token transfer count for an address by token type

    Args:
        session: SQLModel session
        address: Address in hex string format
        token_type: Type of token transfers to count (e.g. "erc20", "erc721")
        columns: Can be "*" for all columns, single column name, or list of column names

    Returns:
        Optional[int]: Transfer count or None if not found

    Raises:
        ValueError: If address format is invalid or token type is not supported
    """
    if isinstance(token_type, str):
        token_type = TokenTransferType(token_type.lower())

    bytes_address = hex_str_to_bytes(address)
    statement = select(TOKEN_TYPE_TO_COLUMN[token_type]).where(AddressIndexStats.address == bytes_address)
    return session.exec(statement).first()


def get_transaction_count(session: Session, address: str, columns: ColumnType = "*") -> Optional[int]:
    """Get total transaction count for an address

    Args:
        session: SQLModel session
        address: Address in hex string format
        columns: Can be "*" for all columns, single column name, or list of column names

    Returns:
        Optional[int]: Transaction count or None if not found

    Raises:
        ValueError: If address format is invalid
    """
    bytes_address = hex_str_to_bytes(address)
    statement = select(AddressIndexStats.transaction_count).where(AddressIndexStats.address == bytes_address)
    return session.exec(statement).first()
