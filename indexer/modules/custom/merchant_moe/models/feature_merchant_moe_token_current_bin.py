from sqlalchemy import Column, Index, PrimaryKeyConstraint, asc, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.modules.custom.merchant_moe.domains.merchant_moe import MerchantMoeTokenCurrentBin


class FeatureMerchantMoeTokenBinCurrentStatus(HemeraModel):
    __tablename__ = "af_merchant_moe_token_bin_current"
    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_timestamp = Column(BIGINT)
    block_number = Column(BIGINT)
    reserve0_bin = Column(NUMERIC(100))
    reserve1_bin = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("position_token_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": MerchantMoeTokenCurrentBin,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_merchant_moe_token_bin_current.block_number",
                "converter": general_converter,
            }
        ]


Index(
    "af_merchant_moe_token_bin_current_token_id_index",
    desc(FeatureMerchantMoeTokenBinCurrentStatus.position_token_address),
    asc(FeatureMerchantMoeTokenBinCurrentStatus.token_id),
)
