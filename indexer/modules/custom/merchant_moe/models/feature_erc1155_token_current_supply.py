from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureErc1155TokenCurrentSupplyStatus(HemeraModel):
    __tablename__ = "af_merchant_moe_token_supply_current"
    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_timestamp = Column(BIGINT)
    block_number = Column(BIGINT)

    total_supply = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("token_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "MerchantMoeErc1155TokenCurrentSupply",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_merchant_moe_token_supply_current.block_number",
                "converter": general_converter,
            }
        ]
