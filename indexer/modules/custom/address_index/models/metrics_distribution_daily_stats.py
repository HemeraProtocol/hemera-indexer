from sqlalchemy import VARCHAR, Column, Date, Double, Numeric, PrimaryKeyConstraint

from common.models import HemeraModel


class AFMetricsDistributionDailyStats(HemeraModel):
    __tablename__ = "af_metrics_distribution_daily_stats"

    distribution_name = Column(VARCHAR, nullable=False)
    block_date = Column(Date, nullable=False)
    avg = Column(Numeric)
    stdev = Column(Numeric)

    __table_args__ = (PrimaryKeyConstraint("distribution_name", "block_date"),)
