from datetime import datetime

from sqlalchemy import DATE, TIMESTAMP, Column, Computed, Index, String, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, JSONB, NUMERIC

from common.models import HemeraModel


class PeriodFeatureDefiCmethAggregates(HemeraModel):
    __tablename__ = "period_feature_defi_cmeth_aggregates"

    period_date = Column(DATE, primary_key=True)
    chain_name = Column(String, primary_key=True)
    protocol_id = Column(String, primary_key=True)

    total_cmeth_balance = Column(NUMERIC)
    total_cmeth_usd = Column(NUMERIC)
    day_user_count = Column(INTEGER)
    total_user_count = Column(INTEGER)
    updated_version = Column(INTEGER)

    create_time = Column(TIMESTAMP, server_default=func.now())


# could be replaced by partition in case of huge amount data
Index("period_feature_defi_cmeth_aggregates_period_date", PeriodFeatureDefiCmethAggregates.period_date)
