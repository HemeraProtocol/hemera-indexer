from datetime import datetime
from sqlalchemy import Column, Index, desc, func
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, INTEGER, BIGINT, TIMESTAMP, NUMERIC, TEXT, BOOLEAN, VARCHAR

from common.models import HemeraModel, general_converter


class Traces(HemeraModel):
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
    reorg = Column(BOOLEAN, default=False)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                'domain': 'Trace',
                'conflict_do_update': False,
                'update_strategy': None,
                'converter': general_converter,
            }
        ]


Index('traces_transaction_hash_index', Traces.transaction_hash)
Index('traces_block_timestamp_index', desc(Traces.block_timestamp))

Index('traces_from_address_block_timestamp_index',
      Traces.from_address, desc(Traces.block_timestamp))

Index('traces_to_address_block_timestamp_index',
      Traces.to_address, desc(Traces.block_timestamp))
