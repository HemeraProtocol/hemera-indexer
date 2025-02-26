from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Index, desc
from sqlmodel import Field

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.address_index.domains import AddressInternalTransaction


class AddressInternalTransactions(HemeraModel, table=True):
    __tablename__ = "address_internal_transactions"

    # Primary key fields
    address: bytes = Field(primary_key=True)
    trace_id: str = Field(primary_key=True)
    block_number: int = Field(primary_key=True)
    transaction_index: int = Field(primary_key=True)
    block_timestamp: datetime = Field(primary_key=True)
    trace_type: Optional[str] = Field(default=None)

    # Additional fields
    related_address: Optional[bytes] = Field(default=None)
    transaction_receipt_status: Optional[int] = Field(default=None)

    # Transaction related fields
    transaction_hash: Optional[bytes] = Field(default=None)
    block_hash: Optional[bytes] = Field(default=None)
    error: Optional[str] = Field(default=None)
    status: Optional[int] = Field(default=None)
    input_method: Optional[str] = Field(default=None)

    # Numerical fields
    value: Optional[Decimal] = Field(default=None, max_digits=100)
    gas: Optional[Decimal] = Field(default=None, max_digits=100)
    gas_used: Optional[Decimal] = Field(default=None, max_digits=100)

    # Type fields
    call_type: Optional[str] = Field(default=None)
    txn_type: Optional[int] = Field(default=None)

    # Metadata fields
    create_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    update_time: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AddressInternalTransaction,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]

    __table_args__ = (
        Index(
            "address_internal_transactions_address_idx",
            "address",
            desc("block_timestamp"),
            desc("block_number"),
            desc("transaction_index"),
            desc("trace_id"),
        ),
    )
