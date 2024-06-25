from datetime import datetime
from sqlalchemy import Column, PrimaryKeyConstraint, Index, desc, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, BIGINT, TIMESTAMP, BOOLEAN
from exporters.jdbc.schema import Base


class Logs(Base):
    __tablename__ = 'logs'

    log_index = Column(INTEGER, primary_key=True)
    address = Column(BYTEA)
    data = Column(BYTEA)
    topic0 = Column(BYTEA)
    topic1 = Column(BYTEA)
    topic2 = Column(BYTEA)
    topic3 = Column(BYTEA)
    transaction_hash = Column(BYTEA, primary_key=True)
    transaction_index = Column(INTEGER)
    block_number = Column(BIGINT)
    block_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    relog = Column(BOOLEAN, default=False)

    __table_args__ = (
        PrimaryKeyConstraint('log_index', 'transaction_hash'),
    )


Index('logs_block_timestamp_index', desc(Logs.block_timestamp))
Index('logs_address_block_number_log_index_index',
      Logs.address, desc(Logs.block_number), desc(Logs.log_index))
