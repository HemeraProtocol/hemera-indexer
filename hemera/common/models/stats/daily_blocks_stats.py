from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field

from hemera.common.models import HemeraModel


class DailyBlocksStats(HemeraModel, table=True):
    __tablename__ = "af_stats_na_daily_blocks"

    # Primary key fields
    block_date: datetime = Field(primary_key=True)  # Assuming block_date is the primary key

    # Numerical fields
    cnt: Optional[int] = Field(default=None)
    avg_size: Optional[Decimal] = Field(default=None)
    avg_gas_limit: Optional[Decimal] = Field(default=None)
    avg_gas_used: Optional[Decimal] = Field(default=None)
    total_gas_used: Optional[int] = Field(default=None)
    avg_gas_used_percentage: Optional[Decimal] = Field(default=None)
    avg_txn_cnt: Optional[Decimal] = Field(default=None)
    total_cnt: Optional[int] = Field(default=None)
    block_interval: Optional[Decimal] = Field(default=None)

    # Timestamp fields
    max_timestamp: Optional[datetime] = Field(default=None)
    min_timestamp: Optional[datetime] = Field(default=None)

    # Metadata fields (Optional)
    create_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    update_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
