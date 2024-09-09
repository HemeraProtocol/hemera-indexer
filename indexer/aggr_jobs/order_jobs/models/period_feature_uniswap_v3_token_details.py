from sqlalchemy import DATE, TIMESTAMP, Column, Computed, Index, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC

from common.models import HemeraModel


class PeriodFeatureUniswapV3TokenDeatils(HemeraModel):
    __tablename__ = "af_uniswap_v3_token_data_period"

    period_date = Column(DATE, primary_key=True, nullable=False)
    nft_address = Column(BYTEA, primary_key=True, nullable=False)
    token_id = Column(INTEGER, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, nullable=False)
    pool_address = Column(BYTEA, nullable=False)
    liquidity = Column(NUMERIC(78))

    create_time = Column(TIMESTAMP, server_default=func.now())


# could be replaced by partition in case of huge amount data
Index("af_uniswap_v3_token_data_period_date_index", PeriodFeatureUniswapV3TokenDeatils.period_date)
