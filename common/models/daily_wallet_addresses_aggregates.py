from sqlalchemy import DATE, Column
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC, VARCHAR

from common.models import HemeraModel


class DailyWalletAddressesAggregates(HemeraModel):
    __tablename__ = "daily_wallet_addresses_aggregates"

    address = Column(BYTEA, primary_key=True)
    block_date = Column(DATE, primary_key=True)

    txn_count = Column(INTEGER, default=0)
    gas_used = Column(NUMERIC(100), default=0)
    contract_deployed_count = Column(INTEGER, default=0)
    unique_address_interacted_count = Column(INTEGER, default=0)
