import os
import requests

from api.app.cache import cache
from decimal import Decimal

base_price_url = os.getenv('BASE_PRICE_HOST', default="https://api.socialscan.io/w3w-price")


@cache.memoize(300)
def get_token_price(symbol, date=None) -> Decimal:
    params = {'symbol': symbol}
    if date:
        params['date'] = date.isoformat()

    response = requests.get(base_price_url, params=params)
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
