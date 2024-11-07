from sqlalchemy import DATE, Column, func, TIMESTAMP, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC, VARCHAR

from common.models import HemeraModel


class PeriodAddressTokenBalances(HemeraModel):
    __tablename__ = "period_address_token_balances"

    period_date = Column(DATE, nullable=False)
    address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(78), primary_key=True)
    token_type = Column(VARCHAR)
    balance = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("address", "token_address", "token_id"),)
