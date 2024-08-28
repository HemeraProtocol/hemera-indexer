from decimal import Decimal

from sqlalchemy import Column, DateTime, Numeric, String

from api.app.cache import cache
from common.models import HemeraModel
from common.models import db as postgres_db
from common.utils.config import get_config

app_config = get_config()


class TokenPrices(HemeraModel):
    symbol = Column(String, primary_key=True)
    timestamp = Column(DateTime, primary_key=True)
    price = Column(Numeric)


class TokenHourlyPrices(HemeraModel):
    symbol = Column(String, primary_key=True)
    timestamp = Column(DateTime, primary_key=True)
    price = Column(Numeric)


@cache.memoize(300)
def get_token_price(symbol, date=None) -> Decimal:
    if date:
        token_price = (
            postgres_db.session.query(TokenHourlyPrices)
            .filter(
                TokenHourlyPrices.symbol == symbol,
                TokenHourlyPrices.timestamp <= date,
            )
            .order_by(TokenHourlyPrices.timestamp.desc())
            .first()
        )
    else:
        token_price = (
            postgres_db.session.query(TokenPrices)
            .filter(TokenPrices.symbol == symbol)
            .order_by(TokenPrices.timestamp.desc())
            .first()
        )
    if token_price:
        return token_price.price
    return Decimal(0.0)
