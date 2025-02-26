from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import Column, desc, func, text
from sqlalchemy.dialects.postgresql import ARRAY, BOOLEAN, INTEGER, JSONB, TIMESTAMP
from sqlmodel import Field, Index

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.contract_internal_transaction import ContractInternalTransaction
from hemera.indexer.domains.trace import Trace


class Traces(HemeraModel, table=True):
    __tablename__ = "traces"

    # Primary key
    trace_id: str = Field(primary_key=True)

    # Address fields
    from_address: Optional[bytes] = Field(default=None)
    to_address: Optional[bytes] = Field(default=None)

    # Value and data fields
    value: Optional[Decimal] = Field(default=None, max_digits=100)
    input: Optional[bytes] = Field(default=None)
    output: Optional[bytes] = Field(default=None)

    # Type fields
    trace_type: Optional[str] = Field(default=None)
    call_type: Optional[str] = Field(default=None)

    # Gas fields
    gas: Optional[Decimal] = Field(default=None, max_digits=100)
    gas_used: Optional[Decimal] = Field(default=None, max_digits=100)

    # Trace specific fields
    subtraces: Optional[int] = Field(default=None)
    trace_address: Optional[List[int]] = Field(default=None, sa_column=Column(ARRAY(INTEGER)))
    error: Optional[str] = Field(default=None)
    status: Optional[int] = Field(default=None)

    # Block fields
    block_number: Optional[int] = Field(default=None)
    block_hash: Optional[bytes] = Field(default=None)
    block_timestamp: Optional[datetime] = Field(default=None)
    transaction_index: Optional[int] = Field(default=None)
    transaction_hash: Optional[bytes] = Field(default=None)

    # Metadata fields
    create_time: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    update_time: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    reorg: bool = Field(default=False, sa_column=Column(BOOLEAN, server_default=text("false")))

    __query_order__ = [block_number, transaction_index]

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": Trace,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]

    __table_args__ = (
        Index("traces_transaction_hash_index", "transaction_hash"),
        Index("traces_block_number_index", desc("block_number")),
        Index(
            "traces_from_address_block_number_index",
            "from_address",
            desc("block_number"),
        ),
        Index(
            "traces_to_address_block_number_index",
            "to_address",
            desc("block_number"),
        ),
    )


class ContractInternalTransactions(HemeraModel, table=True):
    __tablename__ = "contract_internal_transactions"

    # Primary key
    trace_id: str = Field(primary_key=True)

    # Address fields
    from_address: Optional[bytes] = Field(default=None)
    to_address: Optional[bytes] = Field(default=None)

    # Value and data fields
    value: Optional[Decimal] = Field(default=None, max_digits=100)
    input: Optional[bytes] = Field(default=None)
    output: Optional[bytes] = Field(default=None)

    # Type fields
    trace_type: Optional[str] = Field(default=None)
    call_type: Optional[str] = Field(default=None)

    # Gas fields
    gas: Optional[Decimal] = Field(default=None, max_digits=100)
    gas_used: Optional[Decimal] = Field(default=None, max_digits=100)

    # Trace specific fields
    subtraces: Optional[int] = Field(default=None)
    trace_address: Optional[List[int]] = Field(default=None, sa_column=Column(ARRAY(INTEGER)))
    error: Optional[str] = Field(default=None)
    status: Optional[int] = Field(default=None)

    # Block fields
    block_number: Optional[int] = Field(default=None)
    block_hash: Optional[bytes] = Field(default=None)
    block_timestamp: Optional[datetime] = Field(default=None)
    transaction_index: Optional[int] = Field(default=None)
    transaction_hash: Optional[bytes] = Field(default=None)

    # Metadata fields
    create_time: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    update_time: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    reorg: bool = Field(default=False, sa_column=Column(BOOLEAN, server_default=text("false")))

    __query_order__ = [block_number, transaction_index]

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": ContractInternalTransaction,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]

    __table_args__ = (
        Index("contract_internal_transactions_transaction_hash_index", "transaction_hash"),
        Index("contract_internal_transactions_block_number_index", desc("block_number")),
        Index(
            "contract_internal_transactions_from_address_block_number_index",
            "from_address",
            desc("block_number"),
        ),
        Index(
            "contract_internal_transactions_to_address_block_number_index",
            "to_address",
            desc("block_number"),
        ),
    )


class TransactionTraceJson(HemeraModel, table=True):
    __tablename__ = "transaction_trace_json"

    # Primary key
    transaction_hash: bytes = Field(primary_key=True)
    block_timestamp: datetime = Field(primary_key=True)

    block_number: int
    block_hash: bytes
    data: Optional[Dict] = Field(default=None, sa_column=Column(JSONB))
