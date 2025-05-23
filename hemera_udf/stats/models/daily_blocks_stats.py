from sqlalchemy import NUMERIC, Column
from sqlalchemy.dialects.postgresql import BIGINT, DATE

from hemera.common.models import HemeraModel


class DailyBlocksStats(HemeraModel):

    __tablename__ = "af_stats_na_daily_blocks"

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
