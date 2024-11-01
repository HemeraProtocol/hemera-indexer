from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DATE, Column, Index, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC, VARCHAR

from common.models import HemeraModel, general_converter


class PeriodFeatureHoldingBalanceInitCapital(HemeraModel):
    __tablename__ = "period_feature_holding_balance_init_capital"

    period_date = Column(DATE, primary_key=True, nullable=False)
    protocol_id = Column(VARCHAR, primary_key=True)
    position_id = Column(NUMERIC(100), primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, primary_key=True, nullable=False)
    contract_address = Column(BYTEA, primary_key=True, nullable=False)
    token_address = Column(BYTEA, primary_key=True, nullable=False)
    deposit_borrow_type = Column(VARCHAR, primary_key=True, nullable=False)

    token_symbol = Column(VARCHAR)
    balance = Column(NUMERIC)
    create_time = Column(TIMESTAMP, server_default=func.now())
