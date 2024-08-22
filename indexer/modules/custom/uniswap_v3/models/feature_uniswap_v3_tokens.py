from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class UniswapV3Tokens(HemeraModel):
    __tablename__ = "feature_uniswap_v3_tokens"

    nft_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)

    pool_address = Column(BYTEA)
    tick_lower = Column(NUMERIC(100))
    tick_upper = Column(NUMERIC(100))
    fee = Column(NUMERIC(100))

    called_block_number = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("nft_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV3Token",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index("feature_uniswap_v3_tokens_nft_index", UniswapV3Tokens.nft_address)
