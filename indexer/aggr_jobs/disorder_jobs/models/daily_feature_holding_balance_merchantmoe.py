from sqlalchemy import DATE, Column, Computed, Index, String, func, TIMESTAMP
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC

from common.models import HemeraModel


class DailyFeatureHoldingBalanceMerchantmoe(HemeraModel):
    __tablename__ = "daily_feature_holding_balance_merchantmoe"

    block_date = Column(DATE, primary_key=True, nullable=False)
    protocol_id = Column(String, primary_key=True, nullable=False)
    contract_address = Column(BYTEA, primary_key=True, nullable=False)
    token_id = Column(NUMERIC, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, primary_key=True, nullable=False)

    token0_address = Column(String, nullable=False)
    token0_symbol = Column(String, nullable=False)
    token0_balance = Column(NUMERIC(100, 18))

    token1_address = Column(String, nullable=False)
    token1_symbol = Column(String, nullable=False)
    token1_balance = Column(NUMERIC(100, 18))

    create_time = Column(TIMESTAMP, server_default=func.now())
