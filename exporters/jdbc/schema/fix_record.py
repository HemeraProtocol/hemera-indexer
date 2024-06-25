from datetime import datetime

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import INTEGER, BIGINT, VARCHAR, TIMESTAMP

from exporters.jdbc.schema import Base


class FixRecord(Base):
    __tablename__ = 'fix_record'
    job_id = Column(INTEGER, primary_key=True)
    start_block_number = Column(BIGINT)
    last_fixed_block_number = Column(BIGINT)
    remain_process = Column(INTEGER)
    job_status = Column(VARCHAR)
    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP)
