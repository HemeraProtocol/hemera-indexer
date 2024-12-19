from datetime import datetime

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import BIGINT, JSONB, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel


class ExceptionRecords(HemeraModel):
    __tablename__ = "exception_records"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    block_number = Column(BIGINT)
    dataclass = Column(VARCHAR)
    level = Column(VARCHAR)
    message_type = Column(VARCHAR)
    message = Column(VARCHAR)
    exception_env = Column(JSONB)

    record_time = Column(TIMESTAMP, default=datetime.utcnow)
