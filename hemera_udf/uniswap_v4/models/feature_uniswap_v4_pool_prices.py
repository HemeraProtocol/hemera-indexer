from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.uniswap_v4.domains.feature_uniswap_v4 import UniswapV4PoolPrice


class UniswapV4PoolPrices(HemeraModel):
    __tablename__ = "af_uniswap_v4_pool_prices"
    pool_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP, primary_key=True)

    factory_address = Column(BYTEA)

    sqrt_price_x96 = Column(NUMERIC(100))
    tick = Column(NUMERIC(100))

    token0_price = Column(NUMERIC(100))
    token1_price = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("pool_address", "block_number", "block_timestamp"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": UniswapV4PoolPrice,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
