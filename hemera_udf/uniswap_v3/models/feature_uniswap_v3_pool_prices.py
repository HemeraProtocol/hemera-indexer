from sqlalchemy import Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import AgniV3PoolPrice, UniswapV3PoolPrice


class UniswapV3PoolPrices(HemeraModel):
    __tablename__ = "af_uniswap_v3_pool_prices_hist"
    pool_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP, primary_key=True)

    sqrt_price_x96 = Column(NUMERIC(100))
    tick = Column(NUMERIC(100))
    token0_price = Column(NUMERIC)
    token1_price = Column(NUMERIC)

    factory_address = Column(BYTEA)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("pool_address", "block_timestamp", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": UniswapV3PoolPrice,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": AgniV3PoolPrice,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
