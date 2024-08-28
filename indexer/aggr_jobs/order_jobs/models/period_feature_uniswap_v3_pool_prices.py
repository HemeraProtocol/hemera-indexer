from sqlalchemy import DATE, Column, Index, func, TIMESTAMP
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC

from common.models import HemeraModel


class PeriodFeatureUniswapV3PoolPrices(HemeraModel):
    __tablename__ = "period_feature_uniswap_v3_pool_prices"

    period_date = Column(DATE, primary_key=True, nullable=False)
    pool_address = Column(BYTEA, primary_key=True, nullable=False)
    sqrt_price_x96 = Column(NUMERIC(78))

    create_time = Column(TIMESTAMP, server_default=func.now())

# could be replaced by partition in case of huge amount data
Index("Period_feature_uniswap_v3_pool_prices_period_date_index", PeriodFeatureUniswapV3PoolPrices.period_date)
