from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureUniswapV2PoolTotalSupplyRecords(HemeraModel):
    __tablename__ = "feature_uniswap_v2_pool_total_supply_records"
    pool_address = Column(BYTEA, primary_key=True)

    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)
    total_supply = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("pool_address", "block_timestamp", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV2PoolTotalSupply",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]