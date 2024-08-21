from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureErc1155TokenCurrentSupplyStatus(HemeraModel):
    __tablename__ = "feature_erc1155_token_current_supply_status"
    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_timestamp = Column(BIGINT)
    block_number = Column(BIGINT)

    total_supply = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("token_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "MerchantMoeErc1155TokenCurrentSupply",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > feature_erc1155_token_current_supply_status.block_number",
                "converter": general_converter,
            }
        ]
