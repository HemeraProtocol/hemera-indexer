from sqlalchemy import DATE, Column
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER

from common.models import HemeraModel


class DailyContractInteractedAggregates(HemeraModel):
    __tablename__ = "daily_contract_interacted_aggregates"

    block_date = Column(DATE, primary_key=True, nullable=False)
    from_address = Column(BYTEA, primary_key=True, nullable=False)
    to_address = Column(BYTEA, primary_key=True, nullable=False)
    contract_interacted_cnt = Column(INTEGER, default=0)
