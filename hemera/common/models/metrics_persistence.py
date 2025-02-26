from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from hemera.common.models import HemeraModel


class MetricsPersistence(HemeraModel):
    __tablename__ = "metrics_persistence"

    instance: str = Column(primary_key=True)
    metrics: Optional[Dict] = Field(default=None, sa_column=Column(JSONB))

    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)
