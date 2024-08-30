from sqlalchemy import DATE, Column, Index, TIMESTAMP, func, String
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC, VARCHAR

from common.models import HemeraModel


class DailyFeatureHoldingBalanceLendle(HemeraModel):
    __tablename__ = "daily_feature_holding_balance_lendle"

    block_date = Column(DATE, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, primary_key=True)
    protocol_id = Column(VARCHAR, primary_key=True)
    contract_address = Column(BYTEA, primary_key=True)

    token_address = Column(String, nullable=False)
    token_symbol = Column(String, nullable=False)
    token_balance = Column(NUMERIC(78, 18))

    create_time = Column(TIMESTAMP, server_default=func.now())
