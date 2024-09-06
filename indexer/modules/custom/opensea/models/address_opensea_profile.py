from sqlalchemy import NUMERIC, Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, JSONB, TIMESTAMP

from common.models import HemeraModel


class AddressOpenseaProfile(HemeraModel):
    __tablename__ = "af_opensea_profile"

    address = Column(BYTEA, primary_key=True)
    buy_txn_count = Column(BIGINT, default=0)
    sell_txn_count = Column(BIGINT, default=0)
    swap_txn_count = Column(BIGINT, default=0)
    buy_opensea_order_count = Column(BIGINT, default=0)
    sell_opensea_order_count = Column(BIGINT, default=0)
    swap_opensea_order_count = Column(BIGINT, default=0)
    buy_nft_stats = Column(JSONB)
    sell_nft_stats = Column(JSONB)
    buy_volume_usd = Column(NUMERIC)
    sell_volume_usd = Column(NUMERIC)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    first_transaction_hash = Column(BYTEA)
    first_block_timestamp = Column(TIMESTAMP)
    txn_count = Column(BIGINT, default=0)
    opensea_order_count = Column(BIGINT, default=0)
    volume_usd = Column(NUMERIC, default=0)
