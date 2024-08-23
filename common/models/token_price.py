from sqlalchemy import DATE, TIMESTAMP, Column, Index, String
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC

from common.models import HemeraModel


class TokenPrice(HemeraModel):
    __tablename__ = "token_price"

    symbol = Column(String, primary_key=True, nullable=False)
    timestamp = Column(TIMESTAMP, primary_key=True, nullable=False)
    price = Column(NUMERIC(78))
