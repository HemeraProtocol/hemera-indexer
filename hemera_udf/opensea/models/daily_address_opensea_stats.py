from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BYTEA, DATE, INTEGER, JSONB, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel


class DailyAddressOpenseaTransactions(HemeraModel):
    __tablename__ = "af_opensea_daily_transactions"

    address = Column(BYTEA, primary_key=True)
    block_date = Column(DATE, primary_key=True)

    buy_txn_count = Column(INTEGER)
    sell_txn_count = Column(INTEGER)
    swap_txn_count = Column(INTEGER)

    buy_opensea_order_count = Column(INTEGER)
    sell_opensea_order_count = Column(INTEGER)
    swap_opensea_order_count = Column(INTEGER)

    buy_nft_stats = Column(JSONB)
    sell_nft_stats = Column(JSONB)

    buy_volume_crypto = Column(JSONB)
    sell_volume_crypto = Column(JSONB)

    buy_volume_usd = Column(NUMERIC)
    sell_volume_usd = Column(NUMERIC)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
