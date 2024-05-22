from datetime import datetime
from sqlalchemy import Column, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, BIGINT, TIMESTAMP
from exporters.jdbc.schema import Base


class CoinBalances(Base):
    __tablename__ = 'address_coin_balances'

    address = Column(BYTEA, primary_key=True)
    balance = Column(BIGINT)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP)

    __table_args__ = (
        PrimaryKeyConstraint('address', 'block_number'),
    )
