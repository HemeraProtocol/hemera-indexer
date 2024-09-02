from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureUniswapV2LiquidityHoldings(HemeraModel):
    __tablename__ = "feature_uniswap_v2_liquidity_holding_records"
    pool_address = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)

    balance = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("pool_address", "wallet_address", "block_timestamp", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV2LiquidityHolding",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "feature_uniswap_v2_liquidity_holding_records_wallet_b_dindex",
    desc(FeatureUniswapV2LiquidityHoldings.pool_address),
    desc(FeatureUniswapV2LiquidityHoldings.wallet_address),
    desc(FeatureUniswapV2LiquidityHoldings.block_number),
)

Index(
    "feature_uniswap_v2_liquidity_holding_records_pool_b_dindex",
    desc(FeatureUniswapV2LiquidityHoldings.pool_address),
    desc(FeatureUniswapV2LiquidityHoldings.block_number),
)
