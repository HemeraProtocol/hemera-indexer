from sqlalchemy import DATE, Column, Computed, Index
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC

from common.models import HemeraModel


class DailyFeatureUniswapV3TokenDeatils(HemeraModel):
    __tablename__ = "daily_feature_uniswap_v3_token_details"

    nft_address = Column(BYTEA, primary_key=True, nullable=False)
    block_date = Column(DATE, primary_key=True, nullable=False)
    token_id = Column(INTEGER, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, nullable=False)
    pool_address = Column(BYTEA, nullable=False)
    liquidity = Column(NUMERIC(78))


# could be replaced by partition in case of huge amount data
Index("daily_feature_uniswap_v3_token_details_block_date_index", DailyFeatureUniswapV3TokenDeatils.block_date)
