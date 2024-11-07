from datetime import datetime

from sqlalchemy import DATE, TIMESTAMP, Column, Computed, Index, String, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, JSONB, NUMERIC

from common.models import HemeraModel


class PeriodFeatureDefiFbtcAggregates(HemeraModel):
    __tablename__ = "period_feature_defi_fbtc_aggregates"

    period_date = Column(DATE, primary_key=True)
    chain_name = Column(String, primary_key=True)
    protocol_id = Column(String, primary_key=True)

    total_fbtc_balance = Column(NUMERIC)
    total_fbtc_usd = Column(NUMERIC)
    day_user_count = Column(INTEGER)
    total_user_count = Column(INTEGER)
    updated_version = Column(INTEGER)

    create_time = Column(TIMESTAMP, server_default=func.now())


# could be replaced by partition in case of huge amount data
Index("period_feature_defi_fbtc_aggregates_period_date", PeriodFeatureDefiFbtcAggregates.period_date)
