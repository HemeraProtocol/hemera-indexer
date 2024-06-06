from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import VARCHAR, BIGINT, TIMESTAMP

from exporters.jdbc.schema import Base


class SyncRecord(Base):
    __tablename__ = 'sync_record'
    mission_type = Column(VARCHAR, primary_key=True)
    last_block_number = Column(BIGINT)
    update_time = Column(TIMESTAMP)
