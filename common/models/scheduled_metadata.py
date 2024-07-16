from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import INTEGER, VARCHAR

from common.models import db


class ScheduledWalletCountMetadata(db.Model):
    id = Column(INTEGER, primary_key=True)
    dag_id = Column(VARCHAR)
    execution_date = Column(DateTime)
    last_data_timestamp = Column(DateTime)


class ScheduledTokenCountMetadata(db.Model):
    id = Column(INTEGER, primary_key=True)
    dag_id = Column(VARCHAR)
    execution_date = Column(DateTime)
    last_data_timestamp = Column(DateTime)
