from datetime import datetime
from decimal import Decimal
from typing import List

from api.app.cache import cache
from common.models import db
from common.models.token_hourly_price import CoinPrices, TokenHourlyPrices
from common.models.token_prices import TokenPrices
from common.utils.format_utils import as_dict


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


@cache.memoize(300)
def get_coin_prices(date: List[datetime]):
    coin_prices = db.session.query(CoinPrices).filter(CoinPrices.block_date.in_(date)).all()
    return [as_dict(coin_price) for coin_price in coin_prices]


@cache.memoize(300)
def get_latest_coin_prices():
    res = db.session.query(CoinPrices).order_by(CoinPrices.block_date.desc()).first()
    return float(res.price) if res.price else 0.0
