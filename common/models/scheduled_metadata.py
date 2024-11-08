from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import INTEGER, VARCHAR

from common.models import HemeraModel


class ScheduledMetadata(HemeraModel):
    id = Column(INTEGER, primary_key=True)
    dag_id = Column(VARCHAR)
    execution_date = Column(DateTime)
    last_data_timestamp = Column(DateTime)
