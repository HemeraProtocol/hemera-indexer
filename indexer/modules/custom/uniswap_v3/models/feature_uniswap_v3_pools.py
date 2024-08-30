from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class UniswapV3Pools(HemeraModel):
    __tablename__ = "feature_uniswap_v3_pools"
    nft_address = Column(BYTEA, primary_key=True)
    pool_address = Column(BYTEA, primary_key=True)

    token0_address = Column(BYTEA)
    token1_address = Column(BYTEA)
    fee = Column(NUMERIC(100))

    tick_spacing = Column(NUMERIC(100))

    block_number = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("nft_address", "pool_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV3Pool",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "AgniV3Pool",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
