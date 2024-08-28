from datetime import datetime
from typing import Type

from sqlalchemy import Column, Computed, Index, asc, desc, func
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TEXT, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter
from indexer.domain.transaction import Transaction


class Transactions(HemeraModel):
    __tablename__ = "transactions"

    hash = Column(BYTEA, primary_key=True)
    transaction_index = Column(INTEGER)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    value = Column(NUMERIC(100))
    transaction_type = Column(INTEGER)
    input = Column(BYTEA)
    method_id = Column(VARCHAR, Computed("substring((input)::varchar for 8)::bigint::varchar"))
    nonce = Column(INTEGER)

    block_hash = Column(BYTEA)
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    gas = Column(NUMERIC(100))
    gas_price = Column(NUMERIC(100))
    max_fee_per_gas = Column(NUMERIC(100))
    max_priority_fee_per_gas = Column(NUMERIC(100))

    receipt_root = Column(BYTEA)
    receipt_status = Column(INTEGER)
    receipt_gas_used = Column(NUMERIC(100))
    receipt_cumulative_gas_used = Column(NUMERIC(100))
    receipt_effective_gas_price = Column(NUMERIC(100))
    receipt_l1_fee = Column(NUMERIC(100))
    receipt_l1_fee_scalar = Column(NUMERIC(100, 18))
    receipt_l1_gas_used = Column(NUMERIC(100))
    receipt_l1_gas_price = Column(NUMERIC(100))
    receipt_blob_gas_used = Column(NUMERIC(100))
    receipt_blob_gas_price = Column(NUMERIC(100))

    blob_versioned_hashes = Column(ARRAY(BYTEA))
    receipt_contract_address = Column(BYTEA)

    exist_error = Column(BOOLEAN)
    error = Column(TEXT)
    revert_reason = Column(TEXT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "Transaction",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": converter,
            }
        ]


Index("transactions_block_timestamp_index", Transactions.block_timestamp)

Index(
    "transactions_block_number_transaction_index",
    desc(Transactions.block_number),
    desc(Transactions.transaction_index),
)

Index(
    "transactions_from_address_block_number_transaction_idx",
    asc(Transactions.from_address),
    desc(Transactions.block_number),
    desc(Transactions.transaction_index),
)

Index(
    "transactions_to_address_block_number_transaction_idx",
    asc(Transactions.to_address),
    desc(Transactions.block_number),
    desc(Transactions.transaction_index),
)


def converter(table: Type[HemeraModel], data: Transaction, is_update=False):
    converted_data = general_converter(table, data, is_update)
    receipt = data.receipt

    converted_data["receipt_root"] = bytes.fromhex(receipt.root[2:]) if receipt and receipt.root else None
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
        bytes.fromhex(receipt.contract_address[2:]) if receipt and receipt.contract_address else None
    )

    return converted_data
