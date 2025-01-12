from common.models import HemeraModel

from sqlalchemy import Column, Index, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP

class TestUdfDomain(HemeraModel):
    __tablename__ = 'test_job_table'

    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    value = Column(BIGINT)
    token_address = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)
    block_number = Column(BIGINT)
    transaction_hash = Column(BYTEA)
    log_index = Column(BIGINT)

    __table_args__ = (
        PrimaryKeyConstraint('token_address', 'log_index'),
    )

