from exporters.jdbc.schema.tokens import Tokens
from eth_utils import to_normalized_address


def format_token_data(token):
    token = {
        'model': Tokens,
        'address': to_normalized_address(token['address']),
        'name': token['name'],
        'symbol': token['symbol'],
        'total_supply': token['totalSupply'],
        'decimals': token['decimals'],
        'token_type': token['token_type'],
    }
    return token
