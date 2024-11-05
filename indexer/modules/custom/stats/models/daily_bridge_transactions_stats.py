from sqlalchemy import NUMERIC, BigInteger, Column
from sqlalchemy.dialects.postgresql import BIGINT, DATE

from common.models import HemeraModel


class DailyBridgeTransactionsAggregates(HemeraModel):

    __tablename__ = "af_stats_na_daily_bridge_transactions"

    block_date = Column(DATE, primary_key=True)
    deposit_cnt = Column(BigInteger)
    withdraw_cnt = Column(BigInteger)
