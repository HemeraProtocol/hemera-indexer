from datetime import datetime
from sqlalchemy import Column, VARCHAR, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import BYTEA, BIGINT, TIMESTAMP, NUMERIC
from exporters.jdbc.schema import Base


class TokenBalances(Base):
    __tablename__ = 'address_token_balances'

    address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(78))
    token_type = Column(VARCHAR)
    token_address = Column(BYTEA, primary_key=True)
    balance = Column(NUMERIC(100))

    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP)

    __table_args__ = (
        PrimaryKeyConstraint('address', 'token_address', 'block_number'),
    )
