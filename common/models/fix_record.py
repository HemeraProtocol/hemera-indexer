from datetime import datetime

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import BIGINT, INTEGER, TIMESTAMP, VARCHAR

from common.models import HemeraModel


class FixRecord(HemeraModel):
    __tablename__ = "fix_record"
    job_id = Column(INTEGER, primary_key=True)
    start_block_number = Column(BIGINT)
    last_fixed_block_number = Column(BIGINT)
    remain_process = Column(INTEGER)
    job_status = Column(VARCHAR)
    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP)
