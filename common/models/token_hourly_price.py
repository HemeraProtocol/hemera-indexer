from sqlalchemy import Column, DateTime, Numeric, String

from common.models import HemeraModel


class TokenHourlyPrices(HemeraModel):
    symbol = Column(String, primary_key=True)
    timestamp = Column(DateTime, primary_key=True)
    price = Column(Numeric)


class CoinPrices(HemeraModel):
    block_date = Column(DateTime, primary_key=True)
    price = Column(Numeric)
