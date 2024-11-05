from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, TIMESTAMP

from common.models import HemeraModel


class TokenAddressIndexStats(HemeraModel):
    __tablename__ = "af_index_token_address_daily_stats"

    address = Column(BYTEA, primary_key=True)

    token_holder_count = Column(INTEGER)
    token_transfer_count = Column(INTEGER)

    update_time = Column(TIMESTAMP, server_onupdate=func.now())
