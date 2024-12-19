from sqlalchemy import Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.uniswap_v3 import TeahouseLiquidityCurrent


class AfTeahouseLiquidityCurrent(HemeraModel):
    __tablename__ = "af_teahouse_liquidity_current"
    position_token_address = Column(BYTEA, primary_key=True)
    pool_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)

    liquidity = Column(NUMERIC(100))
    tick_lower = Column(NUMERIC(100))
    tick_upper = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("position_token_address", "pool_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": TeahouseLiquidityCurrent,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_teahouse_liquidity_current.block_number",
                "converter": general_converter,
            }
        ]
