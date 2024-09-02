from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class FeatureUniswapV2PoolCurrentReserves(HemeraModel):
    __tablename__ = "feature_uniswap_v2_pool_current_reserves"

    pool_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)

    reserve0 = Column(NUMERIC(100))
    reserve1 = Column(NUMERIC(100))
    block_timestamp_last = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("pool_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV2PoolCurrentReserves",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > feature_uniswap_v2_pool_current_reserves.block_number",
                "converter": general_converter,
            }
        ]
