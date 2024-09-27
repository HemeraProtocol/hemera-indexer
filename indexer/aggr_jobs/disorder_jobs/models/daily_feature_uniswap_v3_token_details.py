from sqlalchemy import Column, Index, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, DATE, INTEGER, NUMERIC, TIMESTAMP

from common.models import HemeraModel


class DailyFeatureUniswapV3TokenDeatils(HemeraModel):
    __tablename__ = "af_uniswap_v3_token_data_daily"

    block_date = Column(DATE, primary_key=True, nullable=False)
    position_token_address = Column(BYTEA, primary_key=True, nullable=False)
    token_id = Column(INTEGER, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, nullable=False)
    pool_address = Column(BYTEA, nullable=False)
    liquidity = Column(NUMERIC(78))

    create_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("block_date", "position_token_address", "token_id"),)


# could be replaced by partition in case of huge amount data
Index("af_uniswap_v3_token_data_daily_index", DailyFeatureUniswapV3TokenDeatils.block_date)
