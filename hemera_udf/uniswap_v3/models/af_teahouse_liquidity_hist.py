from sqlalchemy import Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.uniswap_v3 import TeahouseLiquidityHist


class AfTeahouseLiquidityHist(HemeraModel):
    __tablename__ = "af_teahouse_liquidity_hist"
    position_token_address = Column(BYTEA, primary_key=True)
    pool_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)

    liquidity = Column(NUMERIC(100))
    tick_lower = Column(NUMERIC(100))
    tick_upper = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (
        PrimaryKeyConstraint("position_token_address", "pool_address", "block_timestamp", "block_number"),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": TeahouseLiquidityHist,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
