from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class UniswapV3PoolPrices(HemeraModel):
    __tablename__ = "af_uniswap_v3_pool_prices_hist"
    pool_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)

    sqrt_price_x96 = Column(NUMERIC(100))
    tick = Column(NUMERIC(100))
    factory_address = Column(BYTEA)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("pool_address", "block_timestamp", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV3PoolPrice",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
