from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureUniswapV2PoolCurrentTotalSupplyRecords(HemeraModel):
    __tablename__ = "feature_uniswap_v2_pools_current_total_supply"
    pool_address = Column(BYTEA, primary_key=True)

    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)
    total_supply = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV2PoolCurrentTotalSupply",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > feature_uniswap_v2_pools_current_total_supply.block_number",
                "converter": general_converter,
            }
        ]
