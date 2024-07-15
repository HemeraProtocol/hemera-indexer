from common.models.erc1155_token_holders import ERC1155TokenHolders
from common.models.erc20_token_holders import ERC20TokenHolders
from common.models.erc721_token_holders import ERC721TokenHolders
from eth_utils import to_normalized_address


def format_erc20_token_holder_data(token_balance_dict):
    erc20_token_holder = {
        'model': ERC20TokenHolders,
        'token_address': to_normalized_address(token_balance_dict['token_address']),
        'wallet_address': to_normalized_address(token_balance_dict['address']),
        'balance_of': token_balance_dict['balance'],
        'block_number': token_balance_dict['block_number'],
        'block_timestamp': token_balance_dict['block_timestamp'],
        'update_strategy': "EXCLUDED.block_number >= erc20_token_holders.block_number",
        'update_columns': ['balance_of', 'update_time']
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
        'update_strategy': "EXCLUDED.block_number >= erc721_token_holders.block_number",
        'update_columns': ['balance_of', 'update_time']
    }
    return erc721_token_holder


def format_erc1155_token_holder_data(token_balance_dict):
    erc1155_token_holder = {
        'model': ERC1155TokenHolders,
        'token_address': to_normalized_address(token_balance_dict['token_address']),
        'wallet_address': to_normalized_address(token_balance_dict['address']),
        'token_id': token_balance_dict['token_id'],
        'balance_of': token_balance_dict['balance'],
        'latest_call_contract_time': token_balance_dict['block_timestamp'],
        'block_number': token_balance_dict['block_number'],
        'block_timestamp': token_balance_dict['block_timestamp'],
        'update_strategy': "EXCLUDED.block_number >= erc1155_token_holders.block_number",
        'update_columns': ['balance_of', 'update_time']
    }
    return erc1155_token_holder
