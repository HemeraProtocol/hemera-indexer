from sqlalchemy import ARRAY, BOOLEAN, SMALLINT, Column, String, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, TIMESTAMP

from common.models import HemeraModel


class AggregatorTask(HemeraModel):
    __tablename__ = "aggregator_tasks"
    id = Column(BIGINT, primary_key=True)
    alert_hash = Column(BYTEA, unique=True)
    quorum_numbers = Column(ARRAY(SMALLINT))
    task_index = Column(BIGINT)
    reference_block_number = Column(BIGINT)
    tx_hash = Column(String)
    block_hash = Column(BYTEA)
    block_number = Column(BIGINT)
    transaction_index = Column(BIGINT)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())


class AggregatorTaskSignature(HemeraModel):
    __tablename__ = "aggregator_task_signatures"
    id = Column(BIGINT, primary_key=True)
    alert_hash = Column(BYTEA)
    operator_id = Column(BYTEA)
    sign_result = Column(BOOLEAN)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())
