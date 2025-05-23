from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TEXT, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.uniswap_v4.domains.feature_uniswap_v4 import UniswapV4SwapEvent


class UniswapV4SwapRecords(HemeraModel):
    __tablename__ = "af_uniswap_v4_swap_hist"
    pool_address = Column(BYTEA, primary_key=True)
    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(BIGINT, primary_key=True)

    position_token_address = Column(BYTEA)
    transaction_from_address = Column(BYTEA)
    sender = Column(BYTEA)
    recipient = Column(BYTEA)

    amount0 = Column(NUMERIC(100))
    amount1 = Column(NUMERIC(100))
    token0_price = Column(NUMERIC(100))
    token1_price = Column(NUMERIC(100))
    amount_usd = Column(NUMERIC(100))

    liquidity = Column(NUMERIC(100))
    tick = Column(NUMERIC(100))
    sqrt_price_x96 = Column(NUMERIC(100))

    token0_address = Column(BYTEA)
    token1_address = Column(BYTEA)
    hook_data = Column(TEXT)  # JSON string of hook-related data

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("pool_address", "transaction_hash", "log_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": UniswapV4SwapEvent,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
