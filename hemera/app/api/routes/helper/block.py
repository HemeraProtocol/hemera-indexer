#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/19 18:35
# @Author  ideal93
# @File  block_utils.py.py
# @Brief

from datetime import datetime, timedelta
from typing import Any, List, Optional, Union

from psycopg2._psycopg import Column
from pydantic import BaseModel
from sqlmodel import Session, and_, func, select

from hemera.app.api.routes.helper import process_columns
from hemera.app.utils import ColumnType
from hemera.common.models.blocks import Blocks
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes


# Response Models
class BlockAbbr(BaseModel):
    hash: str
    number: int
    timestamp: datetime
    parent_hash: str
    gas_limit: int
    gas_used: int
    base_fee_per_gas: Optional[int]
    miner: str
    transaction_count: int
    internal_transaction_count: int

    @staticmethod
    def from_db_model(block: Blocks) -> "BlockAbbr":
        return BlockAbbr(
            hash=bytes_to_hex_str(block.hash),
            number=block.number,
            timestamp=block.timestamp,
            parent_hash=bytes_to_hex_str(block.parent_hash),
            gas_limit=int(block.gas_limit),
            gas_used=int(block.gas_used),
            base_fee_per_gas=int(block.base_fee_per_gas) if block.base_fee_per_gas is not None else None,
            miner=bytes_to_hex_str(block.miner),
            transaction_count=block.transactions_count,
            internal_transaction_count=block.internal_transactions_count,
        )


class BlockDetails(BlockAbbr):
    difficulty: Optional[int]
    extra_data: Optional[str]
    gas_fee_token_price: Optional[str]
    is_last_block: Optional[bool]
    nonce: Optional[str]
    receipts_root: Optional[str]
    seconds_since_last_block: Optional[int]
    sha3_uncles: Optional[str]
    size: Optional[int]
    state_root: Optional[str]
    total_difficulty: Optional[int]
    transactions_root: Optional[str]

    @staticmethod
    def from_db_model(block: Blocks) -> "BlockDetails":
        return BlockDetails(
            hash=bytes_to_hex_str(block.hash),
            number=block.number,
            timestamp=block.timestamp,
            parent_hash=bytes_to_hex_str(block.parent_hash),
            gas_limit=int(block.gas_limit),
            gas_used=int(block.gas_used),
            base_fee_per_gas=int(block.base_fee_per_gas) if block.base_fee_per_gas is not None else None,
            miner=bytes_to_hex_str(block.miner),
            transaction_count=block.transactions_count,
            internal_transaction_count=block.internal_transactions_count,
            difficulty=int(block.difficulty) if block.difficulty is not None else None,
            extra_data=bytes_to_hex_str(block.extra_data) if block.extra_data is not None else None,
            gas_fee_token_price=None,
            is_last_block=None,
            nonce=bytes_to_hex_str(block.nonce) if block.nonce is not None else None,
            receipts_root=bytes_to_hex_str(block.receipts_root) if block.receipts_root is not None else None,
            seconds_since_last_block=None,
            sha3_uncles=bytes_to_hex_str(block.sha3_uncles) if block.sha3_uncles is not None else None,
            size=block.size,
            state_root=bytes_to_hex_str(block.state_root) if block.state_root is not None else None,
            total_difficulty=int(block.total_difficulty) if block.total_difficulty is not None else None,
            transactions_root=(
                bytes_to_hex_str(block.transactions_root) if block.transactions_root is not None else None
            ),
        )


def _process_columns(columns: ColumnType):
    return process_columns(Blocks, columns)


def get_block_count(session: Session, duration: timedelta) -> int:
    """
    Calculate the number of blocks within the specified duration (up to 1 hour)
    based on the latest block_timestamp in the Blocks table.

    Args:
        session (Session): SQLModel session object.
        duration (timedelta): Time duration for which to calculate the block count,
                              must not exceed 1 hour.

    Returns:
        int: Number of blocks within the specified time duration.

    Raises:
        ValueError: If the provided duration exceeds 1 hour.
    """
    if duration > timedelta(hours=1):
        raise ValueError("duration must not exceed 1 hour")

    # Retrieve the latest block_timestamp from the Blocks table
    latest_time_stmt = select(func.max(Blocks.timestamp))
    latest_time = session.exec(latest_time_stmt).one()
    if latest_time is None:
        return 0

    start_time = latest_time - duration

    # Count blocks with block_timestamp greater than or equal to start_time
    block_count_stmt = select(func.count()).where(Blocks.timestamp >= start_time)
    block_count = session.exec(block_count_stmt).one()
    return block_count


def _get_last_block(session: Session, columns: ColumnType = "*") -> Optional[Blocks]:
    """Get the latest block

    Args:
        session: SQLModel session
        columns: Can be "*" for all columns, single column name, or list of column names
                Examples:
                - "*": select all columns
                - "number": select only number column
                - "number,hash": select number and hash columns
                - ["number", "hash"]: select number and hash columns

    Returns:
        Optional[Blocks]: Latest block or None
        When specific columns are selected, other attributes will raise AttributeError when accessed
    """
    statement = _process_columns(columns)
    statement = statement.order_by(Blocks.number.desc())
    return session.exec(statement).first()


def _get_block_by_number(session: Session, block_number: int, columns: ColumnType = "*") -> Optional[Blocks]:
    """Get block by block number

    Args:
        session: SQLModel session
        block_number: Block number to query
        columns: Can be "*" for all columns, single column name, or list of column names
                Examples:
                - "*": select all columns
                - "number": select only number column
                - "number,hash": select number and hash columns
                - ["number", "hash"]: select number and hash columns

    Returns:
        Optional[Blocks]: Matching block or None
        When specific columns are selected, other attributes will raise AttributeError when accessed
    """
    statement = _process_columns(columns)
    statement = statement.where(and_(Blocks.number == block_number, Blocks.reorg == False))
    return session.exec(statement).first()


def _get_block_by_hash(session: Session, hash: str, columns: ColumnType = "*") -> Optional[Blocks]:
    """Get block by block hash

    Args:
        session: SQLModel session
        hash: Block hash (hex string)
        columns: Can be "*" for all columns, single column name, or list of column names
                Examples:
                - "*": select all columns
                - "number": select only number column
                - "number,hash": select number and hash columns
                - ["number", "hash"]: select number and hash columns

    Returns:
        Optional[Blocks]: Matching block or None
        When specific columns are selected, other attributes will raise AttributeError when accessed

    Raises:
        ValueError: If hash format is invalid
    """
    statement = _process_columns(columns)
    statement = statement.where(and_(Blocks.hash == hex_str_to_bytes(hash), Blocks.reorg == False))
    return session.exec(statement).first()


def get_block_by_number_or_hash(session: Session, number_or_hash: str) -> Optional[BlockDetails]:
    """Get block by block number or hash

    Args:
        session: SQLModel session
        number_or_hash: Block number or hash

    Returns:
        Optional[BlockDetails]: Matching block or None
    """
    if number_or_hash.isdigit():
        block = _get_block_by_number(session, int(number_or_hash))
    else:
        block = _get_block_by_hash(session, number_or_hash)
    return BlockDetails.from_db_model(block) if block else None


block_list_columns = [
    "hash",
    "number",
    "timestamp",
    "parent_hash",
    "gas_limit",
    "gas_used",
    "base_fee_per_gas",
    "miner",
    "transactions_count",
    "internal_transactions_count",
]


def get_blocks_by_range(
    session: Session,
    start_block: int,
    end_block: int,
) -> List[BlockAbbr]:
    """Get blocks by block number range

    Args:
        session: SQLModel session
        start_block: Start block number
        end_block: End block number

    Returns:
        List[BlockAbbr]: List of matching blocks
    """
    statement = _process_columns(block_list_columns)

    statement = statement.where(
        and_(Blocks.number.between(start_block, end_block), Blocks.reorg == False),
    )
    statement = statement.order_by(Blocks.number.desc())
    blocks = session.exec(statement).all()
    return [BlockAbbr.from_db_model(block) for block in blocks]


def _get_blocks_by_condition(
    session: Session,
    filter_condition: Optional[Any] = None,
    columns: ColumnType = "*",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: Union[Column, List[Column], None] = None,
) -> List[Blocks]:
    """Get blocks by condition with pagination support

    Args:
        session: SQLModel session
        filter_condition: SQL filter condition, defaults to None (no filter)
            for example: Blocks.number > 100
                         Blocks.number.between(100, 200)
                         Blocks.timestamp > datetime(2021, 1, 1)
                         Blocks.hash == hex_str_to_bytes("0x1234")
                         Blocks.hash.in_([hex_str_to_bytes("0x1234"), hex_str_to_bytes("0x5678")])
        columns: Can be "*" for all columns, single column name, or list of column names
                Examples:
                - "*": select all columns
                - "number": select only number column
                - "number,hash": select number and hash columns
                - ["number", "hash"]: select number and hash columns
        limit: Max number of blocks to return
        offset: Number of blocks to skip
        order_by: Specify sort order, can be a single column or list of columns
                Examples:
                - Blocks.number.desc()
                - [Blocks.timestamp.desc(), Blocks.number.asc()]
                - None (defaults to Blocks.number.desc())

    Returns:
        List[Blocks]: List of matching blocks
        When specific columns are selected, other attributes will raise AttributeError when accessed
    """
    statement = _process_columns(columns)

    if filter_condition is not None:
        statement = statement.where(filter_condition)

    if order_by is None:
        statement = statement.order_by(Blocks.number.desc())
    else:
        if isinstance(order_by, list):
            statement = statement.order_by(*order_by)
        else:
            statement = statement.order_by(order_by)

    if limit is not None:
        statement = statement.limit(limit)
    if offset is not None:
        statement = statement.offset(offset)

    return session.exec(statement).all()
