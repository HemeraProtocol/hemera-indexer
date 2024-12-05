from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.modules.custom.merchant_moe.domains.erc1155_token_holding import MerchantMoeErc1155TokenSupply


class FeatureErc1155TokenSupplyRecords(HemeraModel):
    __tablename__ = "af_merchant_moe_token_supply_hist"
    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)

    total_supply = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("position_token_address", "token_id", "block_timestamp", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": MerchantMoeErc1155TokenSupply,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "af_merchant_moe_token_supply_hist_token_block_desc_index",
    desc(FeatureErc1155TokenSupplyRecords.position_token_address),
    desc(FeatureErc1155TokenSupplyRecords.block_timestamp),
)
