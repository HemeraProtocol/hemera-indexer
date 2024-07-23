from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import DATE, BIGINT

from common.models import HemeraModel


class DailyAddressesAggregates(HemeraModel):
    block_date = Column(DATE, primary_key=True)
    active_address_cnt = Column(BIGINT)
    receiver_address_cnt = Column(BIGINT)
    sender_address_cnt = Column(BIGINT)
    total_address_cnt = Column(BIGINT)
    new_address_cnt = Column(BIGINT)
