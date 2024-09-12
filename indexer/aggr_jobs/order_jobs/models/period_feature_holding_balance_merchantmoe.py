from sqlalchemy import Column, Index, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, DATE, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel


class PeriodFeatureHoldingBalanceMerchantmoe(HemeraModel):
    __tablename__ = "af_holding_balance_merchantmoe_period"

    period_date = Column(DATE, primary_key=True, nullable=False)
    protocol_id = Column(VARCHAR, primary_key=True, nullable=False)
    position_token_address = Column(BYTEA, primary_key=True, nullable=False)
    token_id = Column(NUMERIC, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, primary_key=True, nullable=False)

    token0_address = Column(BYTEA, nullable=False)
    token0_symbol = Column(VARCHAR, nullable=False)
    token0_balance = Column(NUMERIC(100, 18))

    token1_address = Column(BYTEA, nullable=False)
    token1_symbol = Column(VARCHAR, nullable=False)
    token1_balance = Column(NUMERIC(100, 18))

    create_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        PrimaryKeyConstraint("period_date", "protocol_id", "position_token_address", "token_id", "wallet_address"),
    )


Index("af_holding_balance_merchantmoe_period_period_date", PeriodFeatureHoldingBalanceMerchantmoe.period_date)
