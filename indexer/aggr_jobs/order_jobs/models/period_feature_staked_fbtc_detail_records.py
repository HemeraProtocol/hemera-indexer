from sqlalchemy import DATE, Column, Index, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC, VARCHAR

from common.models import HemeraModel


class PeriodFeatureStakedFBTCDetailRecords(HemeraModel):
    __tablename__ = "period_feature_staked_fbtc_detail_records"

    period_date = Column(DATE, primary_key=True, nullable=False)
    contract_address = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)

    amount = Column(NUMERIC(100))
    protocol_id = Column(VARCHAR)

    create_time = Column(TIMESTAMP, server_default=func.now())


Index("period_feature_staked_fbtc_detail_records_wallet_period_date", PeriodFeatureStakedFBTCDetailRecords.period_date)
