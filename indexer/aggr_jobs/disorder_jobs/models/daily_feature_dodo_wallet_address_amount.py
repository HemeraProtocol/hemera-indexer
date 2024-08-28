from sqlalchemy import DATE, Column, Computed, Index, String, func, TIMESTAMP
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC

from common.models import HemeraModel


class DailyFeatureUniswapV3WalletAddressAmount(HemeraModel):
    __tablename__ = "daily_feature_uniswap_v3_wallet_address_amount"

    daily_date = Column(DATE, primary_key=True, nullable=False)
    protocol_id = Column(String, primary_key=True, nullable=False)
    contract_address = Column(BYTEA, primary_key=True, nullable=False)
    token_id = Column(INTEGER, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, nullable=False)
    token0_address = Column(String, nullable=False)
    token0_symbol = Column(String, nullable=False)
    token0_balance = Column(NUMERIC(78))

    token1_address = Column(String, nullable=False)
    token1_symbol = Column(String, nullable=False)
    token1_balance = Column(NUMERIC(78))

    create_time = Column(TIMESTAMP, server_default=func.now())


