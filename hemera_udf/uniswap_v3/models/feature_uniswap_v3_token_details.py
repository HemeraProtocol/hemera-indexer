from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.uniswap_v3.domains.feature_uniswap_v3 import AgniV3TokenDetail, UniswapV3TokenDetail


class UniswapV3TokenDetails(HemeraModel):
    __tablename__ = "af_uniswap_v3_token_data_hist"

    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP, primary_key=True)
    wallet_address = Column(BYTEA)
    pool_address = Column(BYTEA)
    liquidity = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("position_token_address", "token_id", "block_timestamp", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": UniswapV3TokenDetail,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": AgniV3TokenDetail,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


Index(
    "af_uniswap_v3_token_data_hist_token_block_desc_index",
    desc(UniswapV3TokenDetails.position_token_address),
    desc(UniswapV3TokenDetails.block_timestamp),
)

Index(
    "af_uniswap_v3_token_data_hist_wallet_token_block_desc_index",
    desc(UniswapV3TokenDetails.wallet_address),
    desc(UniswapV3TokenDetails.position_token_address),
    desc(UniswapV3TokenDetails.block_timestamp),
)
