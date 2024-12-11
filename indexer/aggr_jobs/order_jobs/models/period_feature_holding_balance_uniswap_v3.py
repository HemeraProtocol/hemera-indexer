from sqlalchemy import Column, Index, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, DATE, INTEGER, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel


class PeriodFeatureHoldingBalanceUniswapV3(HemeraModel):
    __tablename__ = "af_holding_balance_uniswap_v3_period"

    period_date = Column(DATE, primary_key=True, nullable=False)
    protocol_id = Column(VARCHAR, primary_key=True, nullable=False)
    pool_address = Column(BYTEA, primary_key=True, nullable=False)
    token_id = Column(INTEGER, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, nullable=False)
    token0_address = Column(BYTEA, nullable=False)
    token0_symbol = Column(VARCHAR, nullable=False)
    token0_balance = Column(NUMERIC(100, 18))

    token1_address = Column(BYTEA, nullable=False)
    token1_symbol = Column(VARCHAR, nullable=False)
    token1_balance = Column(NUMERIC(100, 18))

    create_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("period_date", "protocol_id", "pool_address", "token_id"),)


# could be replaced by partition in case of huge amount data
Index("af_holding_balance_uniswap_v3_period_period_date", PeriodFeatureHoldingBalanceUniswapV3.period_date)
