from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class FeatureUniswapV2CurrentLiquidityHoldings(HemeraModel):
    __tablename__ = "feature_uniswap_v2_liquidity_current_holdings"

    pool_address = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)

    balance = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("wallet_address", "pool_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV2CurrentLiquidityHolding",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > feature_uniswap_v2_liquidity_current_holdings.block_number",
                "converter": general_converter,
            }
        ]


Index(
    "feature_uniswap_v2_liquidity_current_holdings_balance_index",
    FeatureUniswapV2CurrentLiquidityHoldings.pool_address,
    desc(FeatureUniswapV2CurrentLiquidityHoldings.balance),
)
