from sqlalchemy import Column, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import AgniV3SwapEvent, UniswapV3SwapEvent


class UniswapV3PoolSwapRecords(HemeraModel):
    __tablename__ = "af_uniswap_v3_pool_swap_hist"
    pool_address = Column(BYTEA, primary_key=True)
    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP, primary_key=True)
    position_token_address = Column(BYTEA)
    transaction_from_address = Column(BYTEA)
    sender = Column(BYTEA)
    recipient = Column(BYTEA)

    liquidity = Column(NUMERIC(100))
    tick = Column(NUMERIC(100))
    sqrt_price_x96 = Column(NUMERIC(100))
    amount0 = Column(NUMERIC(100))
    amount1 = Column(NUMERIC(100))
    token0_price = Column(NUMERIC)
    token1_price = Column(NUMERIC)
    amount_usd = Column(NUMERIC)

    token0_address = Column(BYTEA)
    token1_address = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("pool_address", "transaction_hash", "log_index", "block_timestamp"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": UniswapV3SwapEvent,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": AgniV3SwapEvent,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
