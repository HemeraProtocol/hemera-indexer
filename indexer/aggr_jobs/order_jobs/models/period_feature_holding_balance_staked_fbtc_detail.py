from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DATE, Column, Index, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC, VARCHAR

from common.models import HemeraModel, general_converter

class PeriodFeatureHoldingBalanceStakedFbtcDetail(HemeraModel):
    __tablename__ = "period_feature_holding_balance_staked_fbtc_detail"

    period_date = Column(DATE, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, primary_key=True)
    protocol_id = Column(VARCHAR, primary_key=True)
    contract_address = Column(BYTEA, primary_key=True)

    balance = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
