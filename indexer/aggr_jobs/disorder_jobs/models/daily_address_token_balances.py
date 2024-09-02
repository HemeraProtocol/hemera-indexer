from sqlalchemy import DATE, Column, TIMESTAMP, func, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC, VARCHAR

from common.models import HemeraModel


class DailyAddressTokenBalances(HemeraModel):
    __tablename__ = "daily_address_token_balances"

    block_date = Column(DATE, primary_key=True, nullable=False)
    address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(78), primary_key=True)
    token_type = Column(VARCHAR)
    balance = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("block_date", "address", "token_address", "token_id"),)
