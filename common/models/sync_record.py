from sqlalchemy import Column, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import BIGINT, INTEGER, TIMESTAMP, VARCHAR

from common.models import HemeraModel


class SyncRecord(HemeraModel):
    __tablename__ = "sync_record"
    mission_sign = Column(VARCHAR, primary_key=True)
    last_block_number = Column(BIGINT)
    update_time = Column(TIMESTAMP)
