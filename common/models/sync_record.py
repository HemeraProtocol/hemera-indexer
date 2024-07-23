from sqlalchemy import Column, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import VARCHAR, BIGINT, TIMESTAMP, INTEGER


from common.models import HemeraModel


class SyncRecord(HemeraModel):
    __tablename__ = 'sync_record'
    mission_type = Column(VARCHAR, primary_key=True)
    entity_types = Column(INTEGER, primary_key=True)
    last_block_number = Column(BIGINT)
    update_time = Column(TIMESTAMP)

    __table_args__ = (
        PrimaryKeyConstraint('mission_type', 'entity_types'),
    )
