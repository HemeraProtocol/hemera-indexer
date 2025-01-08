from sqlalchemy import Column, Date, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import INTEGER

from hemera.common.models import HemeraModel


class AFDashboardDailyAddressStats(HemeraModel):
    __tablename__ = "af_dashboard_daily_address_stats"

    block_date = Column(Date, nullable=False, primary_key=True)
    active_addresses = Column(INTEGER, nullable=False)
    new_addresses = Column(INTEGER)

    __table_args__ = (PrimaryKeyConstraint("block_date"),)
