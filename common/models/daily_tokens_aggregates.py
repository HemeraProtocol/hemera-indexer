from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import DATE, BIGINT, INTEGER

from common.models import HemeraModel


class DailyTokensAggregates(HemeraModel):
    block_date = Column(DATE, primary_key=True)
    erc20_active_address_cnt = Column(INTEGER)
    erc20_total_transfer_cnt = Column(BIGINT)
    erc721_active_address_cnt = Column(INTEGER)
    erc721_total_transfer_cnt = Column(BIGINT)
    erc1155_active_address_cnt = Column(INTEGER)
    erc1155_total_transfer_cnt = Column(BIGINT)
