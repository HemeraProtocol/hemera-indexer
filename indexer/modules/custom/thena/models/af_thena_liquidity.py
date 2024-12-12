from sqlalchemy import INTEGER, Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.modules.custom.thena.domains.feature_thena import ThenaLiquidityDomain


class AfThenaLiquidity(HemeraModel):
    __tablename__ = "af_thena_liquidity"
    pool_address = Column(BYTEA, primary_key=True)
    liquidity = Column(NUMERIC)

    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("pool_address", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": ThenaLiquidityDomain,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
