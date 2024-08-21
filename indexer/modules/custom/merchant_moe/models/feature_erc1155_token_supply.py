from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureErc1155TokenSupplyRecords(HemeraModel):
    __tablename__ = "feature_erc1155_token_supply_records"
    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    called_block_timestamp = Column(BIGINT, primary_key=True)
    called_block_number = Column(BIGINT, primary_key=True)

    total_supply = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (
        PrimaryKeyConstraint("token_address", "token_id", "called_block_timestamp", "called_block_number"),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "MerchantMoeErc1155TokenSupply",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "feature_erc1155_token_supply_token_block_desc_index",
    desc(FeatureErc1155TokenSupplyRecords.token_address),
    desc(FeatureErc1155TokenSupplyRecords.called_block_timestamp),
)
