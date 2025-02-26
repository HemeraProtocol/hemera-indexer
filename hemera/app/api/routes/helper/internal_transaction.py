#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/26 14:28
# @Author  ideal
# @File  internal_transaction.py
# @Brief
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import Session, desc, func, or_, select
from typing_extensions import Literal, Union

from hemera.app.api.routes.helper import ColumnType, process_columns
from hemera.common.enumeration.txn_type import InternalTransactionType
from hemera.common.models.address.address_internal_transaciton import AddressInternalTransactions
from hemera.common.models.traces import ContractInternalTransactions
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes


class InternalTransactionAbbr(BaseModel):
    """Standardized response model for internal transactions"""

    trace_id: str
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    value: Optional[Decimal] = None
    gas: Optional[Decimal] = None
    gas_used: Optional[Decimal] = None
    trace_type: Optional[str] = None
    call_type: Optional[str] = None
    status: Optional[int] = None
    error: Optional[str] = None
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    block_timestamp: Optional[datetime] = None
    transaction_hash: Optional[str] = None
    transaction_index: Optional[int] = None

    @staticmethod
    def from_db_model(
        transaction: Union[ContractInternalTransactions, AddressInternalTransactions]
    ) -> "InternalTransactionAbbr":
        # Common fields between both models
        common_fields = {
            "trace_id": transaction.trace_id,
            "trace_type": transaction.trace_type,
            "call_type": transaction.call_type,
            "value": transaction.value,
            "gas": transaction.gas,
            "gas_used": transaction.gas_used,
            "status": transaction.status,
            "error": transaction.error,
            "block_number": transaction.block_number,
            "block_timestamp": transaction.block_timestamp,
            "transaction_index": transaction.transaction_index,
            "block_hash": bytes_to_hex_str(transaction.block_hash) if transaction.block_hash else None,
            "transaction_hash": (
                bytes_to_hex_str(transaction.transaction_hash) if transaction.transaction_hash else None
            ),
        }

        # Convert bytes fields to hex strings

        if isinstance(transaction, ContractInternalTransactions):
            common_fields["from_address"] = bytes_to_hex_str(transaction.from_address)
            common_fields["to_address"] = bytes_to_hex_str(transaction.to_address)
        else:  # AddressInternalTransactions
            if transaction.txn_type == InternalTransactionType.SENDER.value:
                common_fields["from_address"] = bytes_to_hex_str(transaction.address)
                common_fields["to_address"] = bytes_to_hex_str(transaction.related_address)
            else:
                common_fields["from_address"] = bytes_to_hex_str(transaction.related_address)
                common_fields["to_address"] = bytes_to_hex_str(transaction.address)

        return InternalTransactionAbbr(**common_fields)


def _process_columns(columns: ColumnType):
    return process_columns(ContractInternalTransactions, columns)


def _process_address_columns(columns: ColumnType):
    return process_columns(AddressInternalTransactions, columns)


def get_internal_transactions_by_address(
    session: Session,
    address: Union[str, bytes],
    direction: Optional[Literal["from", "to", "both"]] = "both",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    use_address_index: bool = False,
) -> List[InternalTransactionAbbr]:
    """Unified interface to get internal transactions with option to use address index

    Args:
        session: SQLModel session
        address: Address in hex string format
        direction: Filter direction - "from", "to", or "both" (default)
        limit: Max number of transactions to return
        offset: Number of transactions to skip
        use_address_index: Whether to use address index table (default: False)

    Returns:
        List[InternalTransactionAbbr]: List of standardized transaction responses

    Raises:
        ValueError: If address format is invalid
    """
    if use_address_index:
        raw_transactions = get_internal_transactions_by_address_using_address_index(
            session=session,
            address=address,
            direction=direction,
            columns="*",
            limit=limit,
            offset=offset,
        )
    else:
        raw_transactions = _get_internal_transactions_by_address_native(
            session=session,
            address=address,
            direction=direction,
            columns="*",
            limit=limit,
            offset=offset,
        )

    return [InternalTransactionAbbr.from_db_model(tx) for tx in raw_transactions]


def get_internal_transactions_by_address_using_address_index(
    session: Session,
    address: Union[str, bytes],
    direction: Optional[Literal["from", "to", "both"]] = "both",
    columns: ColumnType = "*",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[AddressInternalTransactions]:
    """Get internal transactions by address with optional direction filter using address index

    Args:
        session: SQLModel session
        address: Address in hex string format
        direction: Filter direction - "from", "to", or "both" (default)
        columns: Can be "*" for all columns, single column name, or list of column names
                Examples:
                - "*": select all columns
                - "block_number": select only block number
                - "block_number,hash": select block number and hash columns
                - ["block_number", "hash"]: select block number and hash columns
        limit: Max number of internal transactions to return
        offset: Number of internal transactions to skip

    Returns:
        List[InternalTransactions]: List of matching transactions
        When specific columns are selected, other attributes will raise AttributeError when accessed

    Raises:
        ValueError: If address format is invalid
    """
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    statement = _process_address_columns(columns).where(AddressInternalTransactions.address == address)

    if direction == "from":
        statement = statement.where(
            AddressInternalTransactions.txn_type.in_(
                [InternalTransactionType.SELF_CALL.value, InternalTransactionType.SENDER.value]
            )
        )
    elif direction == "to":
        statement = statement.where(
            AddressInternalTransactions.txn_type.in_(
                [InternalTransactionType.SELF_CALL.value, InternalTransactionType.RECEIVER.value]
            )
        )
    else:  # both
        statement = statement

    statement = statement.order_by(
        desc(AddressInternalTransactions.block_number),
        desc(AddressInternalTransactions.transaction_index),
        desc(AddressInternalTransactions.trace_id),
    )
    if limit is not None:
        statement = statement.limit(limit)
    if offset is not None:
        statement = statement.offset(offset)

    return session.exec(statement).all()


def _get_internal_transactions_by_address_native(
    session: Session,
    address: Union[str, bytes],
    direction: Optional[Literal["from", "to", "both"]] = "both",
    columns: ColumnType = "*",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[ContractInternalTransactions]:
    """Get internal transactions by address with optional direction filter

    Args:
        session: SQLModel session
        address: Address in hex string format
        direction: Filter direction - "from", "to", or "both" (default)
        columns: Can be "*" for all columns, single column name, or list of column names
                Examples:
                - "*": select all columns
                - "block_number": select only block number
                - "block_number,hash": select block number and hash columns
                - ["block_number", "hash"]: select block number and hash columns
        limit: Max number of internal transactions to return
        offset: Number of internal transactions to skip

    Returns:
        List[InternalTransactions]: List of matching transactions
        When specific columns are selected, other attributes will raise AttributeError when accessed

    Raises:
        ValueError: If address format is invalid
    """
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    statement = _process_columns(columns)

    if direction == "from":
        statement = statement.where(ContractInternalTransactions.from_address == address)
    elif direction == "to":
        statement = statement.where(ContractInternalTransactions.to_address == address)
    else:  # both
        statement = statement.where(
            or_(
                ContractInternalTransactions.from_address == address,
                ContractInternalTransactions.to_address == address,
            )
        )

    statement = statement.order_by(
        desc(ContractInternalTransactions.block_number),
        desc(ContractInternalTransactions.transaction_index),
        desc(ContractInternalTransactions.trace_id),
    )

    if limit is not None:
        statement = statement.limit(limit)
    if offset is not None:
        statement = statement.offset(offset)

    return session.exec(statement).all()


def get_internal_transactions_count_by_address(
    session: Session,
    address: Union[str, bytes],
    direction: Optional[Literal["from", "to", "both"]] = "both",
    use_address_index: bool = False,
) -> int:
    """Get count of internal transactions by address with optional direction filter

    Args:
        session: SQLModel session
        address: Address in hex string format
        direction: Filter direction - "from", "to", or "both" (default)
        use_address_index: Whether to use address index table (default: False)

    Returns:
        int: Count of internal transactions
    """
    if use_address_index:
        internal_transactions_count = get_internal_transactions_count_by_address_using_address_index(
            session=session,
            address=address,
            direction=direction,
        )
    else:
        internal_transactions_count = get_internal_transactions_count_by_address_native(
            session=session,
            address=address,
            direction=direction,
        )

    return internal_transactions_count


def get_internal_transactions_count_by_address_using_address_index(
    session: Session,
    address: Union[str, bytes],
    direction: Optional[Literal["from", "to", "both"]] = "both",
) -> int:
    """Get count of internal transactions by address with optional direction filter using address index

    Args:
        session: SQLModel session
        address: Address in hex string format
        direction: Filter direction - "from", "to", or "both" (default)

    Returns:
        int: Count of internal transactions
    """

    # TODO: Use address index statistics for optimized count
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    statement = (
        select(func.count())
        .select_from(AddressInternalTransactions)
        .where(AddressInternalTransactions.address == address)
    )

    if direction == "from":
        statement = statement.where(
            AddressInternalTransactions.txn_type.in_(
                [InternalTransactionType.SELF_CALL.value, InternalTransactionType.SENDER.value]
            )
        )
    elif direction == "to":
        statement = statement.where(
            AddressInternalTransactions.txn_type.in_(
                [InternalTransactionType.SELF_CALL.value, InternalTransactionType.RECEIVER.value]
            )
        )
    else:  # both
        statement = statement

    return session.exec(statement).first()


def get_internal_transactions_count_by_address_native(
    session: Session,
    address: Union[str, bytes],
    direction: Optional[Literal["from", "to", "both"]] = "both",
) -> int:
    """Get count of internal transactions by address with optional direction filter

    Args:
        session: SQLModel session
        address: Address in hex string format
        direction: Filter direction - "from", "to", or "both" (default)

    Returns:
        int: Count of internal transactions
    """
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    statement = select(func.count()).select_from(ContractInternalTransactions)

    if direction == "from":
        statement = statement.where(ContractInternalTransactions.from_address == address)
    elif direction == "to":
        statement = statement.where(ContractInternalTransactions.to_address == address)
    else:  # both
        statement = statement.where(
            or_(
                ContractInternalTransactions.from_address == address,
                ContractInternalTransactions.to_address == address,
            )
        )

    return session.exec(statement).first()


def get_internal_transactions_by_hash(
    session: Session, transaction_hash: Union[str, bytes], columns: ColumnType = "*"
) -> List[InternalTransactionAbbr]:
    """Get internal transactions by transaction hash

    Args:
        session: SQLModel session
        transaction_hash: Transaction hash in hex string format
        columns: Can be "*" for all columns, single column name, or list of column names
                Examples:
                - "*": select all columns
                - "block_number": select only block number
                - "block_number,hash": select block number and hash columns
                - ["block_number", "hash"]: select block number and hash columns

    Returns:
        List[InternalTransactionAbbr]: List of standardized transaction responses
    """
    if isinstance(transaction_hash, str):
        transaction_hash = hex_str_to_bytes(transaction_hash)

    statement = _process_columns(columns).where(
        ContractInternalTransactions.transaction_hash == hex_str_to_bytes(transaction_hash)
    )

    raw_transactions = session.exec(statement).all()
    return [InternalTransactionAbbr.from_db_model(tx) for tx in raw_transactions]


def get_internal_transactions_count_by_block_number(session: Session, block_number: int) -> int:
    """Get count of internal transactions by block number

    Args:
        session: SQLModel session
        block_number: Block number

    Returns:
        int: Count of internal transactions
    """
    statement = (
        select(func.count())
        .select_from(ContractInternalTransactions)
        .where(ContractInternalTransactions.block_number == block_number)
    )
    return session.exec(statement).first() or 0


def get_internal_transactions_by_block_number(
    session: Session, block_number: int, offset: int, limit: int
) -> List[InternalTransactionAbbr]:
    """Get internal transactions by block number

    Args:
        session: SQLModel session
        block_number: Block number
        offset: Number of transactions to skip
        limit: Max number of transactions to return

    Returns:
        List[InternalTransactionAbbr]: List of standardized transaction responses
    """
    transactions = session.exec(
        select(ContractInternalTransactions)
        .where(ContractInternalTransactions.block_number == block_number)
        .order_by(desc(ContractInternalTransactions.block_number), desc(ContractInternalTransactions.trace_id))
        .offset(offset)
        .limit(limit)
    ).all()

    return [InternalTransactionAbbr.from_db_model(tx) for tx in transactions]


def get_internal_transactions_count(session: Session) -> int:
    """Get count of internal transactions

    Args:
        session: SQLModel session

    Returns:
        int: Count of internal transactions
    """
    statement = select(func.count()).select_from(ContractInternalTransactions)
    return session.exec(statement).first() or 0


def get_internal_transactions(session: Session, offset: int, limit: int) -> List[InternalTransactionAbbr]:
    """Get internal transactions

    Args:
        session: SQLModel session
        offset: Number of transactions to skip
        limit: Max number of transactions to return

    Returns:
        List[InternalTransactionAbbr]: List of standardized transaction responses
    """
    transactions = session.exec(
        select(ContractInternalTransactions)
        .order_by(desc(ContractInternalTransactions.block_number), desc(ContractInternalTransactions.trace_id))
        .offset(offset)
        .limit(limit)
    ).all()

    return [InternalTransactionAbbr.from_db_model(tx) for tx in transactions]
