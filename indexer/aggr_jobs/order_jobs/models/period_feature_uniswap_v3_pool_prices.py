from sqlalchemy import Column, Index, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, DATE, NUMERIC, TIMESTAMP

from common.models import HemeraModel


class PeriodFeatureUniswapV3PoolPrices(HemeraModel):
    __tablename__ = "af_uniswap_v3_pool_prices_period"

    period_date = Column(DATE, primary_key=True, nullable=False)
    pool_address = Column(BYTEA, primary_key=True, nullable=False)
    sqrt_price_x96 = Column(NUMERIC(78))

    create_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("period_date", "pool_address"),)


# could be replaced by partition in case of huge amount data
Index("af_uniswap_v3_pool_prices_period_period_date_index", PeriodFeatureUniswapV3PoolPrices.period_date)
