from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.merchant_moe.domains import MerchantMoePoolRecord


class FeatureMerchantMoePoolRecords(HemeraModel):
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
                "domain": MerchantMoePoolRecord,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
