from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureErc20CurrentTotalSupplyRecords(HemeraModel):
    __tablename__ = "feature_erc20_current_total_supply_records"
    token_address = Column(BYTEA, primary_key=True)

    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)
    total_supply = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "Erc20CurrentTotalSupply",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > feature_erc20_current_total_supply_records.block_number",
                "converter": general_converter,
            }
        ]
