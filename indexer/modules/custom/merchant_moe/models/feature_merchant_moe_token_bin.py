from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureMerChantMoeTokenBinRecords(HemeraModel):
    __tablename__ = "feature_merchant_moe_token_bin_records"
    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    reserve0_bin = Column(NUMERIC(100))
    reserve1_bin = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("token_address", "token_id", "block_timestamp", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "MerChantMoeTokenBin",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "feature_merchant_moe_token_bin_records_token_block_desc_index",
    desc(FeatureMerChantMoeTokenBinRecords.token_address),
    desc(FeatureMerChantMoeTokenBinRecords.block_timestamp),
)
