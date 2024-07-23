from datetime import datetime
from sqlalchemy import Column, Index, desc, func, asc, Computed
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, INTEGER, BIGINT, TIMESTAMP, NUMERIC, BOOLEAN, TEXT, VARCHAR

from common.models import HemeraModel


class Transactions(HemeraModel):
    __tablename__ = 'transactions'

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

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)


Index('transactions_block_timestamp_index', Transactions.block_timestamp)

Index('transactions_block_number_transaction_index',
      desc(Transactions.block_number), desc(Transactions.transaction_index))

Index('transactions_from_address_block_number_transaction_idx',
      asc(Transactions.from_address), desc(Transactions.block_number), desc(Transactions.transaction_index))

Index('transactions_to_address_block_number_transaction_idx',
      asc(Transactions.to_address), desc(Transactions.block_number), desc(Transactions.transaction_index))

