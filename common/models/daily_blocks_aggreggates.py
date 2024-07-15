from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import DATE, BIGINT, NUMERIC

from common.models import db


class DailyBlocksAggregates(db.Model):
    block_date = Column(DATE, primary_key=True)
    cnt = Column(BIGINT)
    avg_size = Column(NUMERIC)
    avg_gas_limit = Column(NUMERIC)
    avg_gas_used = Column(NUMERIC)
    total_gas_used = Column(BIGINT)
    avg_gas_used_percentage = Column(NUMERIC)
    avg_txn_cnt = Column(NUMERIC)
    total_cnt = Column(BIGINT)
    block_interval = Column(NUMERIC)
