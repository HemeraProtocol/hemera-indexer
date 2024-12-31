from sqlalchemy import Column, Index, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class UniswapV3TokenLiquidityRecords(HemeraModel):
    __tablename__ = "af_uniswap_v3_token_liquidity_hist"
    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    transaction_hash = Column(BYTEA)
    owner = Column(BYTEA)

    liquidity = Column(NUMERIC(100))
    amount0 = Column(NUMERIC(100))
    amount1 = Column(NUMERIC(100))

    pool_address = Column(BYTEA)
    token0_address = Column(BYTEA)
    token1_address = Column(BYTEA)

    action_type = Column(VARCHAR)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (
        PrimaryKeyConstraint("position_token_address", "token_id", "block_timestamp", "block_number", "log_index"),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV3TokenUpdateLiquidity",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "AgniV3TokenUpdateLiquidity",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


Index(
    "af_uniswap_v3_token_liquidity_hist_pool_index",
    UniswapV3TokenLiquidityRecords.pool_address,
)
Index(
    "af_uniswap_v3_token_liquidity_hist_token0_index",
    UniswapV3TokenLiquidityRecords.token0_address,
)
Index(
    "af_uniswap_v3_token_liquidity_hist_token1_index",
    UniswapV3TokenLiquidityRecords.token1_address,
)
Index(
    "af_uniswap_v3_token_liquidity_hist_token_id_index",
    UniswapV3TokenLiquidityRecords.token_id,
)
Index(
    "af_uniswap_v3_token_liquidity_hist_owner_index",
    UniswapV3TokenLiquidityRecords.owner,
)
