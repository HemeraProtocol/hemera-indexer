from sqlalchemy import Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.swap.domains.swap_event_domain import (
    FourMemeSwapEvent,
    UniswapV2SwapEvent,
    UniswapV3SwapEvent,
    UniswapV4SwapEvent,
)


class SwapEventModel(HemeraModel):
    __tablename__ = "af_swap_event"

    project = Column(VARCHAR)
    version = Column(INTEGER)

    pool_address = Column(BYTEA, primary_key=True)
    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    block_timestamp = Column(TIMESTAMP, primary_key=True)
    block_number = Column(BIGINT)

    transaction_from_address = Column(BYTEA)
    sender = Column(BYTEA)

    token0_address = Column(BYTEA)
    token1_address = Column(BYTEA)
    amount0 = Column(NUMERIC(100))
    amount1 = Column(NUMERIC(100))
    token0_price = Column(NUMERIC)
    token1_price = Column(NUMERIC)
    amount_usd = Column(NUMERIC)

    # ==== V3 专有字段 ====
    position_token_address = Column(BYTEA)
    recipient = Column(BYTEA)
    liquidity = Column(NUMERIC(100))
    tick = Column(NUMERIC(100))
    sqrt_price_x96 = Column(NUMERIC(100))

    # ==== V2 专有字段 ====
    to_address = Column(BYTEA)
    amount0_in = Column(NUMERIC(100))
    amount1_in = Column(NUMERIC(100))
    amount0_out = Column(NUMERIC(100))
    amount1_out = Column(NUMERIC(100))

    # ==== 系统字段 ====
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("pool_address", "transaction_hash", "log_index", "block_timestamp"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": UniswapV2SwapEvent,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": UniswapV3SwapEvent,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": UniswapV4SwapEvent,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": FourMemeSwapEvent,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
