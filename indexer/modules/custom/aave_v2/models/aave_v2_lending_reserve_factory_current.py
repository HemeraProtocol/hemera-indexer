from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class AaveV2LendingFactorCurrent(HemeraModel):
    __tablename__ = "af_aave_v2_change_factor_current"
    asset_address = Column(BYTEA, primary_key=True)
    factor = Column(BIGINT)

    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("asset_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "AaveV2LendingPoolReserveFactorCurrent",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_aave_v2_change_factor_current.block_number",
                "converter": general_converter,
            },
        ]
