from dataclasses import dataclass

from eth_utils import to_normalized_address
from common.models.token_balances import AddressTokenBalances
from indexer.domain import Domain


@dataclass
class TokenBalance(Domain):
    address: str
    token_id: int
    token_type: str
    token_address: str
    balance: int
    block_number: int
    block_timestamp: int

def format_token_balance_data(token_balance_dict):
    token_transfer = {
        'model': AddressTokenBalances,
        'address': to_normalized_address(token_balance_dict['address']),
        'token_id': token_balance_dict['tokenId'],
        'token_type': token_balance_dict['tokenType'],
        'token_address': to_normalized_address(token_balance_dict['tokenAddress']),
        'balance': token_balance_dict['tokenBalance'],
        'block_number': token_balance_dict['blockNumber'],
        'block_timestamp': token_balance_dict['blockTimestamp']
    }
    return token_transfer
