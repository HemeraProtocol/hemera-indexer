import os
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Type

from sqlalchemy import Column, Computed, text
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, VARCHAR
from sqlmodel import Field, Index

from hemera.common.models import HemeraModel, general_converter
from hemera.common.utils.format_utils import hex_str_to_bytes
from hemera.indexer.domains.transaction import Transaction


class Transactions(HemeraModel, table=True):
    __tablename__ = "transactions"

    # Primary key and transaction basic fields
    hash: bytes = Field(primary_key=True)
    transaction_index: Optional[int] = Field(default=None)
    from_address: Optional[bytes] = Field(default=None)
    to_address: Optional[bytes] = Field(default=None)
    value: Optional[Decimal] = Field(default=None, max_digits=100)
    transaction_type: Optional[int] = Field(default=None)
    input: Optional[bytes] = Field(default=None, sa_column=Column(BYTEA))
    method_id: Optional[str] = Field(
        default=None, sa_column=Column(VARCHAR, Computed("substring((input)::varchar for 8)::bigint::varchar"))
    )
    nonce: Optional[int] = Field(default=None)

    # Block related fields
    block_hash: Optional[bytes] = Field(default=None)
    block_number: Optional[int] = Field(default=None)
    block_timestamp: Optional[datetime] = Field(default=None)

    # Gas related fields
    gas: Optional[Decimal] = Field(default=None, max_digits=100)
    gas_price: Optional[Decimal] = Field(default=None, max_digits=100)
    max_fee_per_gas: Optional[Decimal] = Field(default=None, max_digits=100)
    max_priority_fee_per_gas: Optional[Decimal] = Field(default=None, max_digits=100)

    # Receipt fields
    receipt_root: Optional[bytes] = Field(default=None)
    receipt_status: Optional[int] = Field(default=None)
    receipt_gas_used: Optional[Decimal] = Field(default=None, max_digits=100)
    receipt_cumulative_gas_used: Optional[Decimal] = Field(default=None, max_digits=100)
    receipt_effective_gas_price: Optional[Decimal] = Field(default=None, max_digits=100)
    receipt_l1_fee: Optional[Decimal] = Field(default=None, max_digits=100)
    receipt_l1_fee_scalar: Optional[Decimal] = Field(default=None, max_digits=100, decimal_places=18)
    receipt_l1_gas_used: Optional[Decimal] = Field(default=None, max_digits=100)
    receipt_l1_gas_price: Optional[Decimal] = Field(default=None, max_digits=100)
    receipt_blob_gas_used: Optional[Decimal] = Field(default=None, max_digits=100)
    receipt_blob_gas_price: Optional[Decimal] = Field(default=None, max_digits=100)

    # Blob fields
    blob_versioned_hashes: Optional[List[bytes]] = Field(default=None, sa_column=Column(ARRAY(BYTEA)))
    receipt_contract_address: Optional[bytes] = Field(default=None)

    # Error fields
    exist_error: Optional[bool] = Field(default=None)
    error: Optional[str] = Field(default=None)
    revert_reason: Optional[str] = Field(default=None)

    # Metadata fields
    create_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    update_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    reorg: Optional[bool] = Field(default=False)

    __query_order__ = [block_number, transaction_index]

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": Transaction,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": converter,
            }
        ]

    __table_args__ = (
        Index("transactions_block_timestamp_index", text("block_timestamp DESC")),
        Index("transactions_block_number_transaction_index", text("block_number DESC,transaction_index DESC")),
    )


def converter(table: Type[HemeraModel], data: Transaction, is_update=False):
    converted_data = general_converter(table, data, is_update)
    receipt = data.receipt

    converted_data["receipt_root"] = hex_str_to_bytes(receipt.root) if receipt and receipt.root else None
    converted_data["receipt_status"] = receipt.status if receipt else None
    converted_data["receipt_gas_used"] = receipt.gas_used if receipt else None
    converted_data["receipt_cumulative_gas_used"] = receipt.cumulative_gas_used if receipt else None
    converted_data["receipt_effective_gas_price"] = receipt.effective_gas_price if receipt else None
    converted_data["receipt_l1_fee"] = receipt.l1_fee if receipt else None
    converted_data["receipt_l1_fee_scalar"] = receipt.l1_fee_scalar if receipt else None
    converted_data["receipt_l1_gas_used"] = receipt.l1_gas_used if receipt else None
    converted_data["receipt_l1_gas_price"] = receipt.l1_gas_price if receipt else None
    converted_data["receipt_blob_gas_used"] = receipt.blob_gas_used if receipt else None
    converted_data["receipt_blob_gas_price"] = receipt.blob_gas_price if receipt else None
    converted_data["receipt_contract_address"] = (
        hex_str_to_bytes(receipt.contract_address) if receipt and receipt.contract_address else None
    )

    return converted_data
