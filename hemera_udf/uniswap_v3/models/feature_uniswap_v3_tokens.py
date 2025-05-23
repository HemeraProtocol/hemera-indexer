from sqlalchemy import Column, Index, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import AgniV3Token, UniswapV3Token


class UniswapV3Tokens(HemeraModel):
    __tablename__ = "af_uniswap_v3_tokens"

    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)

    pool_address = Column(BYTEA)
    tick_lower = Column(NUMERIC(100))
    tick_upper = Column(NUMERIC(100))
    fee = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("position_token_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": UniswapV3Token,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": AgniV3Token,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


Index("af_uniswap_v3_tokens_nft_index", UniswapV3Tokens.position_token_address)
