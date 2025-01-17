from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import JSON, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel


class MetricsPersistence(HemeraModel):
    __tablename__ = "metrics_persistence"

    instance = Column(VARCHAR, primary_key=True)
    metrics = Column(JSON)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
