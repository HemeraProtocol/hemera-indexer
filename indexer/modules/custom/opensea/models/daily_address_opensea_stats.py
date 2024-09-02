from sqlalchemy import INT, NUMERIC, Column, Date, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, JSON, JSONB, SMALLINT, TIMESTAMP

from common.models import HemeraModel


class DailyAddressOpenseaTransactions(HemeraModel):
    __tablename__ = "af_opensea_daily_transactions"

    address = Column(BYTEA, primary_key=True)
    related_address = Column(BYTEA)
    transaction_type = Column(SMALLINT)

    block_date = Column(Date, primary_key=True)

    buy_txn_count = Column(INT)
    sell_txn_count = Column(INT)
    swap_txn_count = Column(INT)

    buy_txn_volume_crypto = Column(JSONB)
    sell_txn_volume_crypto = Column(JSONB)

    buy_txn_volume_usd = Column(NUMERIC)
    sell_txn_volume_usd = Column(NUMERIC)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
