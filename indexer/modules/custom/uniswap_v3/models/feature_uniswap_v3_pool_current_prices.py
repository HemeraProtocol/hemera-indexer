from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class UniswapV3PoolCurrentPrices(HemeraModel):
    __tablename__ = "feature_uniswap_v3_pool_current_prices"
    pool_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)

    sqrt_price_x96 = Column(NUMERIC(100))
    tick = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV3PoolCurrentPrice",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > feature_uniswap_v3_pool_current_prices.block_number",
                "converter": general_converter,
            }
        ]
