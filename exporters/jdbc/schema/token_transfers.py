from datetime import datetime
from sqlalchemy import Column, VARCHAR
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, BIGINT, TIMESTAMP, NUMERIC
from exporters.jdbc.schema import Base


class TokenTransfers(Base):
    __tablename__ = 'token_transfers'

    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    amount = Column(NUMERIC(78))
    token_id = Column(NUMERIC(78))
    token_type = Column(VARCHAR)
    token_address = Column(BYTEA)

    block_number = Column(BIGINT)
    block_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP)
