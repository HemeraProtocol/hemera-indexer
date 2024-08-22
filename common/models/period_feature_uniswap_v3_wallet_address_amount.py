from sqlalchemy import DATE, Column, Computed, Index, String
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC

from common.models import HemeraModel


class PeriodFeatureUniswapV3WalletAddressAmount(HemeraModel):
    __tablename__ = "period_feature_uniswap_v3_wallet_address_amount"

    contract_address = Column(BYTEA, primary_key=True, nullable=False)
    period_date = Column(DATE, primary_key=True, nullable=False)
    token_id = Column(INTEGER, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, nullable=False)
    token0_address = Column(String, nullable=False)
    token0_symbol = Column(String, nullable=False)
    token0_balance = Column(NUMERIC(78))
    token0_price = Column(NUMERIC(78))
    token0_price_value = Column(NUMERIC(78))

    token1_address = Column(String, nullable=False)
    token1_symbol = Column(String, nullable=False)
    token1_balance = Column(NUMERIC(78))
    token1_price = Column(NUMERIC(78))
    token1_price_value = Column(NUMERIC(78))


# could be replaced by partition in case of huge amount data
Index("period_feature_uniswap_v3_wallet_address_amount_period_date",
      PeriodFeatureUniswapV3WalletAddressAmount.period_date)
