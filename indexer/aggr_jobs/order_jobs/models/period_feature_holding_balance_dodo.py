from sqlalchemy import DATE, TIMESTAMP, Column, Computed, Index, String, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC

from common.models import HemeraModel


class PeriodFeatureHoldingBalanceDoDo(HemeraModel):
    __tablename__ = "period_feature_holding_balance_dodo"

    period_date = Column(DATE, primary_key=True, nullable=False)
    protocol_id = Column(String, primary_key=True, nullable=False)
    contract_address = Column(BYTEA, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, primary_key=True, nullable=False)

    balance_of = Column(NUMERIC(100, 18))
    total_supply = Column(NUMERIC(100, 18))

    token0_address = Column(BYTEA, nullable=False)
    token0_symbol = Column(String, nullable=False)
    token0_balance = Column(NUMERIC(100, 18))

    token1_address = Column(BYTEA, nullable=False)
    token1_symbol = Column(String, nullable=False)
    token1_balance = Column(NUMERIC(100, 18))

    create_time = Column(TIMESTAMP, server_default=func.now())
