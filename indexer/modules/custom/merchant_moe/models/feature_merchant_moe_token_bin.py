from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureMerchantMoeTokenBinRecords(HemeraModel):
    __tablename__ = "af_merchant_moe_token_bin_hist"
    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    reserve0_bin = Column(NUMERIC(100))
    reserve1_bin = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("position_token_address", "token_id", "block_timestamp", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "MerchantMoeTokenBin",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "af_merchant_moe_token_bin_hist_token_block_desc_index",
    desc(FeatureMerchantMoeTokenBinRecords.position_token_address),
    desc(FeatureMerchantMoeTokenBinRecords.block_timestamp),
)
