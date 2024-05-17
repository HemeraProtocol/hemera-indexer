from datetime import datetime
from sqlalchemy import Column, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, BIGINT, TIMESTAMP
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
    update_time = Column(TIMESTAMP)

    __table_args__ = (
        PrimaryKeyConstraint('log_index', 'transaction_hash'),
    )
