from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class UniswapV3TokenDetails(HemeraModel):
    __tablename__ = "feature_uniswap_v3_token_details"

    nft_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    called_block_number = Column(BIGINT, primary_key=True)
    called_block_timestamp = Column(BIGINT, primary_key=True)
    wallet_address = Column(BYTEA)
    pool_address = Column(BYTEA)
    liquidity = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("nft_address", "token_id", "called_block_timestamp", "called_block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV3TokenDetail",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "feature_uniswap_v3_token_details_token_block_desc_index",
    desc(UniswapV3TokenDetails.nft_address),
    desc(UniswapV3TokenDetails.called_block_timestamp),
)

Index(
    "feature_uniswap_v3_token_details_wallet_token_block_desc_index",
    desc(UniswapV3TokenDetails.wallet_address),
    desc(UniswapV3TokenDetails.nft_address),
    desc(UniswapV3TokenDetails.called_block_timestamp),
)
