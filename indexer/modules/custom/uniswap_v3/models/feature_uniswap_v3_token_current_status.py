from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class UniswapV3TokenCurrentStatus(HemeraModel):
    __tablename__ = "af_uniswap_v3_token_data_current"

    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)
    wallet_address = Column(BYTEA)
    pool_address = Column(BYTEA)
    liquidity = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("position_token_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV3TokenCurrentStatus",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_uniswap_v3_token_data_current.block_number",
                "converter": general_converter,
            },
            {
                "domain": "AgniV3TokenCurrentStatus",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_uniswap_v3_token_data_current.block_number",
                "converter": general_converter,
            },
        ]


Index(
    "af_uniswap_v3_token_data_current_wallet_desc_index",
    desc(UniswapV3TokenCurrentStatus.wallet_address),
)
