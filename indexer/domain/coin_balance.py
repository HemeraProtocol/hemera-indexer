from common.models.coin_balances import CoinBalances
from eth_utils import to_normalized_address


def format_coin_balance_data(coin_balance_dict):
    coin_balance = {
        'model': CoinBalances,
        'address': to_normalized_address(coin_balance_dict['address']),
        'balance': coin_balance_dict['balance'],
        'block_number': coin_balance_dict['block_number'],
        'block_timestamp': coin_balance_dict['block_timestamp']
    }

    return coin_balance
