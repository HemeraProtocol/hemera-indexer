import logging

from enumeration.token_type import TokenType
from exporters.jdbc.schema.erc1155_token_holders import ERC1155TokenHolders
from exporters.jdbc.schema.erc20_token_holders import ERC20TokenHolders
from exporters.jdbc.schema.erc721_token_holders import ERC721TokenHolders
from utils.utils import hex_to_dec, to_normalized_address
from exporters.jdbc.schema.token_balances import TokenBalances


def format_erc20_token_holder_data(token_balance_dict):
    erc20_token_holder = {
        'model': ERC20TokenHolders,
        'token_address': to_normalized_address(token_balance_dict['token_address']),
        'wallet_address': to_normalized_address(token_balance_dict['address']),
        'balance_of': token_balance_dict['balance'],
        'block_number': token_balance_dict['block_number'],
        'block_timestamp': token_balance_dict['block_timestamp'],
        'update_strategy': "EXCLUDED.block_number >= erc20_token_holders.block_number"
    }
    return erc20_token_holder


def format_erc721_token_holder_data(token_balance_dict):
    erc721_token_holder = {
        'model': ERC721TokenHolders,
        'token_address': to_normalized_address(token_balance_dict['token_address']),
        'wallet_address': to_normalized_address(token_balance_dict['address']),
        'balance_of': token_balance_dict['balance'],
        'block_number': token_balance_dict['block_number'],
        'block_timestamp': token_balance_dict['block_timestamp'],
        'update_strategy': "EXCLUDED.block_number >= erc721_token_holders.block_number"
    }
    return erc721_token_holder


def format_erc1155_token_holder_data(token_balance_dict):
    erc1155_token_holder = {
        'model': ERC1155TokenHolders,
        'token_address': to_normalized_address(token_balance_dict['token_address']),
        'wallet_address': to_normalized_address(token_balance_dict['address']),
        'token_id': token_balance_dict['token_id'],
        'balance_of': token_balance_dict['balance'],
        'last_call_contract_time': token_balance_dict['block_timestamp'],
        'block_number': token_balance_dict['block_number'],
        'block_timestamp': token_balance_dict['block_timestamp'],
        'update_strategy': "EXCLUDED.block_number >= erc1155_token_holders.block_number"
    }
    return erc1155_token_holder
