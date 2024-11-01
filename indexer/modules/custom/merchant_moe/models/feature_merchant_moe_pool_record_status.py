from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureMerChantMoePoolRecordStatus(HemeraModel):
    __tablename__ = "af_merchant_moe_pool_data_current"
    pool_address = Column(BYTEA, primary_key=True)
    block_timestamp = Column(BIGINT)
    block_number = Column(BIGINT)
    active_id = Column(BIGINT)
    bin_step = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("pool_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "MerChantMoePoolCurrentStatus",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_merchant_moe_pool_data_current.block_number",
                "converter": general_converter,
            }
        ]
