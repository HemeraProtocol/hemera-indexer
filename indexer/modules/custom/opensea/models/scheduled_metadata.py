from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, VARCHAR

from common.models import HemeraModel


class ScheduledMetadata(HemeraModel):
    __tablename__ = "af_opensea_na_scheduled_metadata"

    id = Column(INTEGER, primary_key=True)
    dag_id = Column(VARCHAR)
    execution_date = Column(TIMESTAMP)
    last_data_timestamp = Column(TIMESTAMP)
