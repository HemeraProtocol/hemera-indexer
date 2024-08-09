from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, JSONB, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureBlueChipHolders(HemeraModel):
    __tablename__ = "feature_blue_chip_holders"
    wallet_address = Column(BYTEA, primary_key=True)

    hold_detail = Column(JSONB)

    current_count = Column(BIGINT)

    called_block_number = Column(BIGINT)
    called_block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "BlueChipHolder",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
