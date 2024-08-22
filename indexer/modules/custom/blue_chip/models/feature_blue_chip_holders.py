from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, JSONB, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureBlueChipHolders(HemeraModel):
    __tablename__ = "feature_blue_chip_holders"
    wallet_address = Column(BYTEA, primary_key=True)

    hold_detail = Column(JSONB)

    current_count = Column(BIGINT)

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

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
