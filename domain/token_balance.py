import logging

from enumeration.token_type import TokenType
from utils.utils import hex_to_dec, to_normalized_address
from exporters.jdbc.schema.token_balances import TokenBalances


def format_token_balance_data(token_balance_dict):
    token_transfer = {
        'model': TokenBalances,
        'address': to_normalized_address(token_balance_dict['address']),
        'token_id': token_balance_dict['tokenId'],
        'token_type': token_balance_dict['tokenType'],
        'token_address': to_normalized_address(token_balance_dict['tokenAddress']),
        'balance': token_balance_dict['tokenBalance'],
        'block_number': hex_to_dec(token_balance_dict['blockNumber']),
        'block_timestamp': hex_to_dec(token_balance_dict['blockTimestamp'])
    }
    return token_transfer
