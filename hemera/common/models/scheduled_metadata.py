from datetime import datetime
from typing import Optional

from sqlmodel import Field

from hemera.common.models import HemeraModel, general_converter


class ScheduledMetadata(HemeraModel, table=True):
    __tablename__ = "af_index_na_scheduled_metadata"

    # Primary key and basic fields
    id: int = Field(primary_key=True)
    dag_id: Optional[str] = Field(default=None)
    execution_date: Optional[datetime] = Field(default=None)
    last_data_timestamp: Optional[datetime] = Field(default=None)

    # Metadata fields
    create_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    update_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
