from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import BIGINT, DATE

from hemera.common.models import HemeraModel


class DailyBridgeTransactionsAggregates(HemeraModel, table=True):
    __tablename__ = "af_stats_na_daily_bridge_transactions"

    block_date = Column(DATE, primary_key=True)
    deposit_cnt = Column(BIGINT)
    withdraw_cnt = Column(BIGINT)
