from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DATE, Column, Index, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC, VARCHAR

from common.models import HemeraModel, general_converter


class PeriodFeatureHoldingBalanceLendle(HemeraModel):
    __tablename__ = "period_feature_holding_balance_lendle"

    period_date = Column(DATE, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, primary_key=True)
    protocol_id = Column(VARCHAR, primary_key=True)
    contract_address = Column(BYTEA, primary_key=True)

    token_symbol = Column(VARCHAR)
    token_address = Column(VARCHAR)

    balance = Column(NUMERIC(78, 18))

    create_time = Column(TIMESTAMP, server_default=func.now())
