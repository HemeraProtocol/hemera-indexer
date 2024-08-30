from sqlalchemy import DATE, Column, Index, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC, VARCHAR

from common.models import HemeraModel


class DailyFeatureHoldingBalanceStakedFbtcDetail(HemeraModel):
    __tablename__ = "daily_feature_holding_balance_staked_fbtc_detail"

    block_date = Column(DATE, primary_key=True, nullable=False)
    wallet_address = Column(BYTEA, primary_key=True)
    protocol_id = Column(VARCHAR, primary_key=True)
    contract_address = Column(BYTEA, primary_key=True)

    balance = Column(NUMERIC(78, 18))

    create_time = Column(TIMESTAMP, server_default=func.now())
