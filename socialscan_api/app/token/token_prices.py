from decimal import Decimal

from socialscan_api.app.cache import cache



@cache.memoize(300)
def get_token_price(symbol, date=None) -> Decimal:

    return Decimal(0.0)
