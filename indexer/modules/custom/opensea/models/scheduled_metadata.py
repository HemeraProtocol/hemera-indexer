from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import TIMESTAMP

from common.models import HemeraModel


class ScheduledMetadata(HemeraModel):
    __tablename__ = "af_opensea_na_scheduled_metadata"

    id = Column(Integer, primary_key=True)
    dag_id = Column(String)
    execution_date = Column(TIMESTAMP)
    last_data_timestamp = Column(TIMESTAMP)
