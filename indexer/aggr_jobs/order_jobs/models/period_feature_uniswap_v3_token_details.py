from sqlalchemy import DATE, Column, Computed, Index, func, TIMESTAMP
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC

from common.models import HemeraModel


class PeriodFeatureUniswapV3TokenDeatils(HemeraModel):
    __tablename__ = "period_feature_uniswap_v3_token_details"

    period_date = Column(DATE, primary_key=True, nullable=False)
    nft_address = Column(BYTEA, primary_key=True, nullable=False)
    token_id = Column(INTEGER, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, nullable=False)
    pool_address = Column(BYTEA, nullable=False)
    liquidity = Column(NUMERIC(78))

    create_time = Column(TIMESTAMP, server_default=func.now())


# could be replaced by partition in case of huge amount data
Index("daily_feature_uniswap_v3_token_details_period_date_index", PeriodFeatureUniswapV3TokenDeatils.period_date)
