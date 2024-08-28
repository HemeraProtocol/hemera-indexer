from datetime import datetime

from sqlalchemy import DATE, TIMESTAMP, Column, Computed, Index, String, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, JSONB, NUMERIC

from common.models import HemeraModel


class PeriodFeatureDefiWalletFbtcDetail(HemeraModel):
    __tablename__ = "period_feature_defi_wallet_fbtc_detail"

    period_date = Column(DATE, primary_key=True)
    wallet_address = Column(String, primary_key=True)
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

    create_time = Column(TIMESTAMP, server_default=func.now())


# could be replaced by partition in case of huge amount data
Index("period_feature_uniswap_v3_wallet_fbtc_detail_period_date", PeriodFeatureDefiWalletFbtcDetail.period_date)
