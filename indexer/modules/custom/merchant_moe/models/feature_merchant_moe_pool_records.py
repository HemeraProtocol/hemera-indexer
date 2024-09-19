from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureMerChantMoePoolRecords(HemeraModel):
    __tablename__ = "af_merchant_moe_pool_data_hist"
    pool_address = Column(BYTEA, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    active_id = Column(BIGINT)
    bin_step = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("pool_address", "block_timestamp", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "MerChantMoePoolRecord",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
