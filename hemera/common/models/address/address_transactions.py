from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import SMALLINT
from sqlmodel import Field, Index

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.address_index import AddressTransaction


class AddressTransactions(HemeraModel, table=True):
    __tablename__ = "address_transactions"

    # Primary key fields
    address: bytes = Field(primary_key=True)
    block_number: int = Field(primary_key=True)
    transaction_index: int = Field(primary_key=True)
    block_timestamp: datetime = Field(primary_key=True)

    # Transaction related fields
    transaction_hash: Optional[bytes] = Field(default=None)
    block_hash: Optional[bytes] = Field(default=None)
    txn_type: Optional[int] = Field(default=None, sa_column=Column(SMALLINT))
    related_address: Optional[bytes] = Field(default=None)
    value: Optional[Decimal] = Field(default=None, max_digits=100)
    transaction_fee: Optional[Decimal] = Field(default=None, max_digits=100)
    receipt_status: Optional[int] = Field(default=None)
    method: Optional[str] = Field(default=None)

    # Metadata fields
    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)

    __query_order__ = [block_number, transaction_index]

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AddressTransaction,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]

    __table_args__ = (
        Index(
            "address_transactions_address_block_timestamp_block_number_t_idx",
            text("address, block_timestamp DESC, block_number DESC, transaction_index DESC"),
        ),
        Index(
            "address_transactions_address_txn_type_block_timestamp_block_idx",
            text("address, txn_type, block_timestamp DESC, block_number DESC, transaction_index DESC"),
        ),
    )
