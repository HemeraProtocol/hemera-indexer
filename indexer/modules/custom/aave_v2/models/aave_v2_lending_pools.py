from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class AaveV2LendingPools(HemeraModel):
    __tablename__ = "af_aave_v2_lending_pools"
    asset_address = Column(BYTEA, primary_key=True)
    a_token_address = Column(BYTEA)
    stable_debt_token_address = Column(BYTEA)
    variable_debt_token_address = Column(BYTEA)
    interest_rate_strategy_address = Column(BYTEA)
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
                "domain": "AaveV2LendingPool",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
