#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/31 13:54
# @Author  ideal93
# @File  log.py
# @Brief
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from sqlmodel import Session, desc, select

from hemera.app.core.service import extra_contract_service
from hemera.app.utils import ColumnType
from hemera.common.models.logs import Logs
from hemera.common.utils.abi_code_utils import decode_log_data
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes


class LogDetails(BaseModel):
    # Transaction related fields
    transaction_hash: str

    # Log specific fields
    log_index: int
    address: str
    data: str
    topic0: str
    topic1: Optional[str] = None
    topic2: Optional[str] = None
    topic3: Optional[str] = None

    # Block related fields
    block_number: int
    block_hash: str
    block_timestamp: datetime

    @staticmethod
    def from_db_model(log: Logs) -> "LogDetails":
        return LogDetails(
            transaction_hash=bytes_to_hex_str(log.transaction_hash),
            log_index=log.log_index,
            address=bytes_to_hex_str(log.address),
            data=bytes_to_hex_str(log.data),
            topic0=bytes_to_hex_str(log.topic0),
            topic1=bytes_to_hex_str(log.topic1) if log.topic1 else None,
            topic2=bytes_to_hex_str(log.topic2) if log.topic2 else None,
            topic3=bytes_to_hex_str(log.topic3) if log.topic3 else None,
            block_number=log.block_number,
            block_hash=bytes_to_hex_str(log.block_hash),
            block_timestamp=log.block_timestamp,
        )


class DecodedInputData(BaseModel):
    """Decoded input data for a log parameter"""

    indexed: bool
    name: str = ""
    data_type: str
    hex_data: str
    dec_data: str


class ContractFunctionInfo(BaseModel):
    address_display_name: Optional[str] = None
    function_name: Optional[str] = None
    full_function_name: Optional[str] = None
    function_unsigned: Optional[str] = None
    input_data: List[DecodedInputData] = []


class LogItem(LogDetails, ContractFunctionInfo):
    def __init__(self, log_details: LogDetails, contract_info: ContractFunctionInfo):
        """
        Initialize LogItem by combining LogDetails and ContractInfo.

        Args:
            log_details (LogDetails): The LogDetails instance.
            contract_info (ContractFunctionInfo): The ContractInfo instance.
        """
        combined_data = {**log_details.dict(), **contract_info.dict()}
        super().__init__(**combined_data)


def _process_log_columns(columns: ColumnType):
    """Process columns for Logs table"""
    if columns == "*":
        return select(Logs)

    if isinstance(columns, str):
        columns = columns.split(",")

    columns = [col.strip() for col in columns]
    return select(*[getattr(Logs, col) for col in columns])


def _get_logs_by_hash(session: Session, hash: str, columns: ColumnType = "*") -> List[Logs]:
    """Get logs by transaction hash

    Args:
        session: SQLModel session
        hash: Transaction hash (hex string) or bytes
        columns: Can be "*" for all columns, single column name, or list of column names
                Examples:
                - "*": select all columns from logs
                - "address,data": select specific columns
                - ["address", "data"]: select specific columns

    Returns:
        List[Logs]: List of logs matching the transaction hash
        When specific columns are selected, only those columns will be available

    Raises:
        ValueError: If hash format is invalid
    """
    if isinstance(hash, str):
        hash = hex_str_to_bytes(hash.lower())

    statement = _process_log_columns(columns)
    statement = statement.where(Logs.transaction_hash == hash)

    return session.exec(statement).all()


def _get_logs_by_address(
    session: Session, address: Union[str, bytes], columns: ColumnType = "*", limit: int = 25, offset: int = 0
) -> List[Logs]:
    """Get logs by contract address

    Args:
        session: SQLModel session
        address: Contract address (hex string) or bytes
        columns: Can be "*" for all columns, single column name, or list of column names
                Examples:
                - "*": select all columns from logs
                - "address,data": select specific columns
                - ["address", "data"]: select specific columns
        limit: Max number of logs to return
        offset: Number of logs to skip

    Returns:
        List[Logs]: List of logs matching the contract address
        When specific columns are selected, only those columns will be available

    Raises:
        ValueError: If address format is invalid
    """
    if isinstance(address, str):
        address = hex_str_to_bytes(address.lower())

    statement = _process_log_columns(columns)
    statement = statement.where(Logs.address == address).order_by(desc(Logs.block_number), desc(Logs.log_index))

    statement = statement.limit(limit)
    statement = statement.offset(offset)

    return session.exec(statement).all()


def get_logs_by_hash(session: Session, hash: str) -> List[LogDetails]:
    """Get logs by transaction hash

    Args:
        session: SQLModel session
        hash: Transaction hash (hex string)

    Returns:
        List[LogDetails]: List of logs matching the transaction hash
        When specific columns are selected, only those columns will be available
    """
    logs = _get_logs_by_hash(session, hash, "*")
    return [LogDetails.from_db_model(log) for log in logs]


def get_logs_by_address(session: Session, address: str, limit: int = 25, offset: int = 0) -> List[LogDetails]:
    """Get logs by contract address

    Args:
        session: SQLModel session
        address: Contract address (hex string)
        limit: Max number of logs to return
        offset: Number of logs to skip
    Returns:
        List[LogDetails]: List of logs matching the contract address
        When specific columns are selected, only those columns will be available
    """
    logs = _get_logs_by_address(session, address, "*", limit, offset)
    return [LogDetails.from_db_model(log) for log in logs]
