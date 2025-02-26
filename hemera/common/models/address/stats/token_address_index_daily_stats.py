from datetime import datetime

from sqlmodel import Field

from hemera.common.models import HemeraModel


class TokenAddressIndexStats(HemeraModel, table=True):
    __tablename__ = "af_index_token_address_daily_stats"

    address: bytes = Field(primary_key=True)
    token_holder_count: int = Field()
    token_transfer_count: int = Field()

    update_time: datetime = Field(default_factory=datetime.utcnow)
