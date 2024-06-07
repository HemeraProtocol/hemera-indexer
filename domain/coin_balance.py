from exporters.jdbc.schema.coin_balances import CoinBalances
from eth_utils import to_normalized_address, to_int


def format_coin_balance_data(coin_balance_dict):
    coin_balance = {
        'model': CoinBalances,
        'address': to_normalized_address(coin_balance_dict['address']),
        'balance': coin_balance_dict['balance'],
        'block_number': to_int(hexstr=coin_balance_dict['block_number']),
        'block_timestamp': to_int(hexstr=coin_balance_dict['block_timestamp'])
    }

    return coin_balance
