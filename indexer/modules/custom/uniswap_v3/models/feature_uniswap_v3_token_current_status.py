from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class UniswapV3TokenCurrentStatus(HemeraModel):
    __tablename__ = "feature_uniswap_v3_token_current_status"

    nft_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)
    wallet_address = Column(BYTEA)
    pool_address = Column(BYTEA)
    liquidity = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("nft_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV3TokenCurrentStatus",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > feature_uniswap_v3_token_current_status.block_number",
                "converter": general_converter,
            }
        ]


Index(
    "feature_uniswap_v3_token_current_status_wallet_desc_index",
    desc(UniswapV3TokenCurrentStatus.wallet_address),
)
