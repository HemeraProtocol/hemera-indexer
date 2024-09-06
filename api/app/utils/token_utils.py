from decimal import Decimal

from api.app.cache import cache
from common.models import db
from common.models.token_hourly_price import TokenHourlyPrices
from common.models.token_prices import TokenPrices


@cache.memoize(300)
def get_token_price(symbol, date=None) -> Decimal:
    if date:
        token_price = (
            db.session.query(TokenHourlyPrices)
            .filter(
                TokenHourlyPrices.symbol == symbol,
                TokenHourlyPrices.timestamp <= date,
            )
            .order_by(TokenHourlyPrices.timestamp.desc())
            .first()
        )
    else:
        token_price = (
            db.session.query(TokenPrices)
            .filter(TokenPrices.symbol == symbol)
            .order_by(TokenPrices.timestamp.desc())
            .first()
        )
    if token_price:
        return token_price.price
    return Decimal(0.0)
