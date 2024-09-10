from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureMerChantMoePools(HemeraModel):
    __tablename__ = "af_merchant_moe_pools"
    token_address = Column(BYTEA, primary_key=True)
    block_timestamp = Column(BIGINT)
    block_number = Column(BIGINT)
    token0_address = Column(BYTEA)
    token1_address = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("token_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "MerChantMoePool",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
