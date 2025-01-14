from sqlalchemy import INTEGER, Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.uniswap_v2.domains import UniswapV2SwapEvent


class AfUniswapV2SwapEvent(HemeraModel):
    __tablename__ = "af_uniswap_v2_swap_event"
    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    transaction_from_address = Column(BYTEA)

    pool_address = Column(BYTEA)
    sender = Column(BYTEA)
    to_address = Column(BYTEA)

    amount0_in = Column(NUMERIC)
    amount1_in = Column(NUMERIC)
    amount0_out = Column(NUMERIC)
    amount1_out = Column(NUMERIC)

    amount0 = Column(NUMERIC)
    amount1 = Column(NUMERIC)
    token0_price = Column(NUMERIC)
    token1_price = Column(NUMERIC)
    amount_usd = Column(NUMERIC)

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP, primary_key=True)

    token0_address = Column(BYTEA)
    token1_address = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("transaction_hash", "log_index", "block_timestamp"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": UniswapV2SwapEvent,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
