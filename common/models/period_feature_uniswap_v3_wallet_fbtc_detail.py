from datetime import datetime

from sqlalchemy import DATE, Column, Computed, Index, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC, JSONB

from common.models import HemeraModel


class PeriodFeatureUniswapV3WalletFbtcDetail(HemeraModel):
    __tablename__ = "period_feature_uniswap_v3_wallet_fbtc_detail"

    wallet_address = Column(String, primary_key=True)
    period_date = Column(INTEGER, primary_key=True)
    chain_name = Column(String, primary_key=True)
    contracts = Column(JSONB)

    total_fbtc_balance = Column(NUMERIC)
    total_fbtc_usd = Column(NUMERIC)
    wallet_holding_fbtc_balance = Column(NUMERIC)
    wallet_holding_fbtc_usd = Column(NUMERIC)
    updated_version = Column(INTEGER)
    total_protocol_fbtc_balance = Column(NUMERIC)
    total_protocol_fbtc_usd = Column(NUMERIC)
    rank = Column(INTEGER)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())


# could be replaced by partition in case of huge amount data
Index("period_feature_uniswap_v3_wallet_fbtc_detail_period_date",
      PeriodFeatureUniswapV3WalletFbtcDetail.period_date)
