from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import (
    UniswapV3Pool,
    UniswapV3PoolFromSwapEvent,
    UniswapV3PoolFromToken,
)


class UniswapV3Pools(HemeraModel):
    __tablename__ = "af_uniswap_v3_pools"
    position_token_address = Column(BYTEA, primary_key=True)
    pool_address = Column(BYTEA, primary_key=True)

    factory_address = Column(BYTEA)

    token0_address = Column(BYTEA)
    token1_address = Column(BYTEA)
    fee = Column(NUMERIC(100))

    tick_spacing = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("position_token_address", "pool_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": UniswapV3Pool,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": UniswapV3PoolFromSwapEvent,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": UniswapV3PoolFromToken,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
