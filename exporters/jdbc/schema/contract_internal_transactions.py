from datetime import datetime
from sqlalchemy import Column, VARCHAR, Index, desc, func
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, INTEGER, BIGINT, TIMESTAMP, NUMERIC, TEXT, BOOLEAN
from exporters.jdbc.schema import Base


class ContractInternalTransactions(Base):
    __tablename__ = 'contract_internal_transactions'

    trace_id = Column(VARCHAR, primary_key=True)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    value = Column(NUMERIC(100))
    trace_type = Column(VARCHAR)
    call_type = Column(VARCHAR)
    gas = Column(NUMERIC(100))
    gas_used = Column(NUMERIC(100))
    trace_address = Column(ARRAY(INTEGER))
    error = Column(TEXT)
    status = Column(INTEGER)
    block_number = Column(BIGINT)
    block_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)
    transaction_index = Column(INTEGER)
    transaction_hash = Column(BYTEA)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)


Index('contract_internal_transactions_transaction_hash_idx', ContractInternalTransactions.transaction_hash)
Index('internal_transactions_block_timestamp_index', desc(ContractInternalTransactions.block_timestamp))
Index('internal_transactions_address_number_transaction_index',
      ContractInternalTransactions.from_address, ContractInternalTransactions.to_address,
      desc(ContractInternalTransactions.block_number), desc(ContractInternalTransactions.transaction_index))
