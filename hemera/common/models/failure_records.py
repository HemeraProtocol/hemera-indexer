from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import BIGINT, JSON, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel


class FailureRecords(HemeraModel):
    __tablename__ = "failure_records"
    record_id = Column(BIGINT, primary_key=True, autoincrement=True)
    mission_sign = Column(VARCHAR)
    output_types = Column(VARCHAR)
    start_block_number = Column(BIGINT)
    end_block_number = Column(BIGINT)
    exception_stage = Column(VARCHAR)
    exception = Column(JSON)
    crash_time = Column(TIMESTAMP)
