from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureErc20CurrentTotalSupplyRecords(HemeraModel):
    __tablename__ = "af_erc20_total_supply_current"
    token_address = Column(BYTEA, primary_key=True)

    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)
    total_supply = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "Erc20CurrentTotalSupply",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_erc20_total_supply_current.block_number",
                "converter": general_converter,
            }
        ]
