from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DATE, TIMESTAMP, Column, Computed, Index, String, create_engine, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC

from common.models import HemeraModel, general_converter

# db = SQLAlchemy(session_options={"autoflush": False})


class PeriodFeatureHoldingBalanceUniswapV3(HemeraModel):
    __tablename__ = "af_holding_balance_uniswap_v3_period"

    period_date = Column(DATE, primary_key=True, nullable=False)
    protocol_id = Column(String, primary_key=True, nullable=False)
    contract_address = Column(BYTEA, primary_key=True, nullable=False)
    token_id = Column(INTEGER, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, nullable=False)
    token0_address = Column(BYTEA, nullable=False)
    token0_symbol = Column(String, nullable=False)
    token0_balance = Column(NUMERIC(100, 18))

    token1_address = Column(BYTEA, nullable=False)
    token1_symbol = Column(String, nullable=False)
    token1_balance = Column(NUMERIC(100, 18))

    create_time = Column(TIMESTAMP, server_default=func.now())


# could be replaced by partition in case of huge amount data
Index("af_holding_balance_uniswap_v3_period_period_date", PeriodFeatureHoldingBalanceUniswapV3.period_date)
