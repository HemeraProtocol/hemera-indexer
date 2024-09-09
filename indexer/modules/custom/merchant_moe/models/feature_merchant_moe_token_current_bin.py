from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, asc, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureMerChantMoeTokenBinCurrentStatus(HemeraModel):
    __tablename__ = "feature_merchant_moe_token_bin_current_status"
    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_timestamp = Column(BIGINT)
    block_number = Column(BIGINT)
    reserve0_bin = Column(NUMERIC(100))
    reserve1_bin = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("token_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "MerChantMoeTokenCurrentBin",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > feature_merchant_moe_token_bin_current_status.block_number",
                "converter": general_converter,
            }
        ]


Index(
    "feature_merchant_moe_token_bin_current_status_token_id_index",
    desc(FeatureMerChantMoeTokenBinCurrentStatus.token_address),
    asc(FeatureMerChantMoeTokenBinCurrentStatus.token_id),
)
