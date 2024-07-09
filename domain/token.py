from exporters.jdbc.schema.tokens import Tokens
from eth_utils import to_normalized_address


def format_token_data(token):
    format_token = {
        'model': Tokens,
        'address': to_normalized_address(token['address']),
        'token_type': token['token_type'],
        'total_supply': token['totalSupply'],
        'update_block_number': token['block_number'],
        'update_strategy': "EXCLUDED.update_block_number > tokens.update_block_number",
        'update_columns': ['total_supply', 'update_block_number', 'update_time'],
    }

    if 'name' in token:
        format_token['name'] = token['name']

    if 'symbol' in token:
        format_token['symbol'] = token['symbol']

    if 'decimals' in token:
        format_token['decimals'] = token['decimals']

    return format_token
