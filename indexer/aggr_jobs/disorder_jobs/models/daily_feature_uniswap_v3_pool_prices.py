from sqlalchemy import DATE, Column, Computed, Index
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC

from common.models import HemeraModel


class DailyFeatureUniswapV3PoolPrices(HemeraModel):
    __tablename__ = "daily_feature_uniswap_v3_pool_prices"

    pool_address = Column(BYTEA, primary_key=True, nullable=False)
    block_date = Column(DATE, primary_key=True, nullable=False)
    sqrt_price_x96 = Column(NUMERIC(78))


# could be replaced by partition in case of huge amount data
Index("daily_feature_uniswap_v3_pool_prices_block_date_index", DailyFeatureUniswapV3PoolPrices.block_date)
