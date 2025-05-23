from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.uniswap_v4.domains.feature_uniswap_v4 import UniswapV4PoolCurrentPrice


class UniswapV4PoolCurrentPrices(HemeraModel):
    __tablename__ = "af_uniswap_v4_pool_current_prices"
    pool_address = Column(BYTEA, primary_key=True)

    factory_address = Column(BYTEA)

    sqrt_price_x96 = Column(NUMERIC(100))
    tick = Column(NUMERIC(100))

    token0_price = Column(NUMERIC(100))
    token1_price = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("pool_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": UniswapV4PoolCurrentPrice,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
