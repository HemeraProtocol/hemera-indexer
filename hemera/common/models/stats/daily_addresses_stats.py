from datetime import datetime
from typing import Optional

from sqlmodel import Field

from hemera.common.models import HemeraModel


class DailyAddressesStats(HemeraModel, table=True):
    __tablename__ = "af_stats_na_daily_addresses"

    # Primary key fields
    block_date: datetime = Field(primary_key=True)

    # Numerical fields
    active_address_cnt: Optional[int] = Field(default=None)
    receiver_address_cnt: Optional[int] = Field(default=None)
    sender_address_cnt: Optional[int] = Field(default=None)
    total_address_cnt: Optional[int] = Field(default=None)
    new_address_cnt: Optional[int] = Field(default=None)

    # Metadata fields (Optional)
    create_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    update_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
