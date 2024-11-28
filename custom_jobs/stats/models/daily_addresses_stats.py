from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import BIGINT, DATE

from common.models import HemeraModel


class DailyAddressesStats(HemeraModel):

    __tablename__ = "af_stats_na_daily_addresses"

    block_date = Column(DATE, primary_key=True)
    active_address_cnt = Column(BIGINT)
    receiver_address_cnt = Column(BIGINT)
    sender_address_cnt = Column(BIGINT)
    total_address_cnt = Column(BIGINT)
    new_address_cnt = Column(BIGINT)
