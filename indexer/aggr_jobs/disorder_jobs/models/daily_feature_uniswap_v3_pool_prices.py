from sqlalchemy import DATE, TIMESTAMP, Column, Computed, Index, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC

from common.models import HemeraModel


class DailyFeatureUniswapV3PoolPrices(HemeraModel):
    __tablename__ = "af_uniswap_v3_pool_prices_daily"

    block_date = Column(DATE, primary_key=True, nullable=False)
    pool_address = Column(BYTEA, primary_key=True, nullable=False)

    sqrt_price_x96 = Column(NUMERIC(78))

    create_time = Column(TIMESTAMP, server_default=func.now())


# could be replaced by partition in case of huge amount data
Index("af_uniswap_v3_pool_prices_daily_block_date_index", DailyFeatureUniswapV3PoolPrices.block_date)
