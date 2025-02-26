from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Index, desc
from sqlmodel import Field

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.address_index.domains import AddressContractOperation


class AddressContractOperations(HemeraModel, table=True):
    __tablename__ = "address_contract_operations"

    # Metadata fields
    address: bytes = Field(primary_key=True)
    trace_id: str = Field(primary_key=True)
    block_number: int = Field(primary_key=True)
    transaction_index: int = Field(primary_key=True)
    block_timestamp: datetime = Field(primary_key=True)

    trace_from_address: Optional[bytes] = Field(default=None)
    contract_address: Optional[bytes] = Field(default=None)
    transaction_hash: Optional[bytes] = Field(default=None)
    block_hash: Optional[bytes] = Field(default=None)
    error: Optional[str] = Field(default=None)
    status: Optional[int] = Field(default=None)
    gas: Optional[Decimal] = Field(default=None)
    gas_used: Optional[Decimal] = Field(default=None)
    trace_type: Optional[str] = Field(default=None)
    call_type: Optional[str] = Field(default=None)
    transaction_receipt_status: Optional[int] = Field(default=None)

    # Metadata fields
    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AddressContractOperation,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]

    __table_args__ = (
        Index(
            "address_contract_operations_address_block_tn_t_idx",
            "address",
            desc("block_timestamp"),
            desc("block_number"),
            desc("transaction_index"),
        ),
    )
