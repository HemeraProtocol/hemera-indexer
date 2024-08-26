from datetime import datetime

from sqlalchemy import Column, DATE, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC

from common.models import HemeraModel


class PeriodFeatureErc1155TokenHoldings(HemeraModel):
    __tablename__ = "period_feature_erc1155_token_holdings"

    period_date = Column(DATE, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)

    balance = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
