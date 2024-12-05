from sqlalchemy import Column, DateTime, Numeric, String

from hemera.common.models import HemeraModel


class TokenPrices(HemeraModel):
    symbol = Column(String, primary_key=True)
    timestamp = Column(DateTime, primary_key=True)
    price = Column(Numeric)
