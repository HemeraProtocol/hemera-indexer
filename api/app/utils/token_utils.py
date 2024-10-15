import logging
import os
import requests

from api.app.cache import cache
from decimal import Decimal

logger = logging.getLogger(__name__)

base_price_url = os.getenv('BASE_PRICE_HOST', default="https://api.socialscan.io/price-test/v1/token/price")
price_auth = os.getenv('PRICE_AUTHENTICATION', '')
if not price_auth:
    logger.warning("PRICE_AUTHENTICATION is not set, price will not be fetched")


@cache.memoize(300)
def get_token_price(symbol, date=None) -> Decimal:
    if not price_auth:
        return Decimal(0.0)
    params = {'symbol': symbol}
    if date:
        params['date'] = date.isoformat()

    response = requests.get(base_price_url, params=params, headers={"Authorization": price_auth})
    response.raise_for_status()
    data = response.json()
    return Decimal(data['price'])


def get_token_price_map_by_symbol_list(token_symbol_list):
    token_price_map = {}
    for symbol in token_symbol_list:
        token_price = get_token_price(symbol)
        if token_price:
            token_price_map[symbol] = token_price.price
    return token_price_map
