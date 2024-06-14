from datetime import datetime
from sqlalchemy import Column, VARCHAR, Index, desc, func
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, INTEGER, BIGINT, TIMESTAMP, NUMERIC, TEXT
from exporters.jdbc.schema import Base


class Traces(Base):
    __tablename__ = 'traces'

    trace_id = Column(VARCHAR, primary_key=True)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    value = Column(NUMERIC(100))
    input = Column(BYTEA)
    output = Column(BYTEA)
    trace_type = Column(VARCHAR)
    call_type = Column(VARCHAR)
    gas = Column(NUMERIC(100))
    gas_used = Column(NUMERIC(100))
    subtraces = Column(INTEGER)
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


Index('traces_transaction_hash_index', Traces.transaction_hash)

Index('traces_address_block_timestamp_index',
      Traces.from_address, Traces.to_address, desc(Traces.block_timestamp))
