from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.modules.custom.merchant_moe.domains.erc1155_token_holding import (
    MerchantMoeErc1155TokenCurrentSupply,
)


class FeatureErc1155TokenCurrentSupplyStatus(HemeraModel):
    __tablename__ = "af_merchant_moe_token_supply_current"
    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_timestamp = Column(BIGINT)
    block_number = Column(BIGINT)

    total_supply = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("position_token_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": MerchantMoeErc1155TokenCurrentSupply,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_merchant_moe_token_supply_current.block_number",
                "converter": general_converter,
            }
        ]
