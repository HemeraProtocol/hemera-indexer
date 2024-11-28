from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class AfErc20TotalSupplyHist(HemeraModel):
    __tablename__ = "af_erc20_total_supply_hist"
    token_address = Column(BYTEA, primary_key=True)

    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)
    total_supply = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("token_address", "block_timestamp", "block_number"),)

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
