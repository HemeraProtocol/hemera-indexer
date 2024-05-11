from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import BYTEA, BIGINT, TIMESTAMP, NUMERIC, BOOLEAN

from exporters.jdbc.schema import Base


class Blocks(Base):
    __tablename__ = 'blocks'
    hash = Column(BYTEA, primary_key=True)
    number = Column(BIGINT)
    timestamp = Column(TIMESTAMP)
    parent_hash = Column(BYTEA)
    nonce = Column(BYTEA)

    gas_limit = Column(NUMERIC(100))
    gas_used = Column(NUMERIC(100))
    base_fee_per_gas = Column(NUMERIC(100))

    difficulty = Column(NUMERIC(38))
    total_difficulty = Column(NUMERIC(38))
    size = Column(BIGINT)
    miner = Column(BYTEA)
    sha3_uncles = Column(BYTEA)
    transactions_root = Column(BYTEA)
    transactions_count = Column(BIGINT)

    state_root = Column(BYTEA)
    receipts_root = Column(BYTEA)
    extra_data = Column(BYTEA)
    withdrawals_root = Column(BYTEA)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP)
    data_confirmed = Column(BOOLEAN, default=False)
