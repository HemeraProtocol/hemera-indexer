from datetime import datetime
from sqlalchemy import Column, Index, desc, func
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, INTEGER, BIGINT, TIMESTAMP, NUMERIC, BOOLEAN, TEXT

from common.models import db


class Transactions(db.Model):
    __tablename__ = 'transactions'

    hash = Column(BYTEA, primary_key=True)
    transaction_index = Column(INTEGER)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    value = Column(NUMERIC(100))
    transaction_type = Column(INTEGER)
    input = Column(BYTEA)
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


Index('transactions_block_timestamp_block_number_index',
      desc(Transactions.block_timestamp), desc(Transactions.block_number))

Index('transactions_address_block_number_transaction_idx',
      Transactions.from_address, Transactions.to_address,
      desc(Transactions.block_number), desc(Transactions.transaction_index))
