from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureErc20TotalSupplyRecords(HemeraModel):
    __tablename__ = "feature_erc20_total_supply_records"
    token_address = Column(BYTEA, primary_key=True)

    called_block_number = Column(BIGINT, primary_key=True)
    called_block_timestamp = Column(BIGINT, primary_key=True)
    total_supply = Column(BIGINT)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("token_address", "called_block_timestamp", "called_block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "Erc20TotalSupply",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
