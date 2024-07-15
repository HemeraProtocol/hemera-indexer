from eth_utils import to_normalized_address

from common.models.erc1155_token_id_details import ERC1155TokenIdDetails
from common.models.erc721_token_id_changes import ERC721TokenIdChanges
from common.models.erc721_token_id_details import ERC721TokenIdDetails


def format_erc721_token_id_change(token_id_info):
    erc721_token_id_change = {
        'model': ERC721TokenIdChanges,
        'address': to_normalized_address(token_id_info['address']),
        'token_id': token_id_info['token_id'],
        'token_owner': token_id_info['ownerOf'],
        'block_number': token_id_info['block_number'],
        'block_timestamp': token_id_info['block_timestamp']
    }
    return erc721_token_id_change


def format_erc721_token_id_detail(token_id_info):
    erc721_token_id_detail = {
        'model': ERC721TokenIdDetails,
        'address': to_normalized_address(token_id_info['address']),
        'token_id': token_id_info['token_id'],
        'token_owner': token_id_info['ownerOf'],
        'token_uri_info': None,
        'block_number': token_id_info['block_number'],
        'block_timestamp': token_id_info['block_timestamp'],
        'update_strategy': "EXCLUDED.block_number >= erc721_token_id_details.block_number",
        'update_columns': ['token_owner', 'block_number', 'block_timestamp', 'update_time']
    }

    if 'tokenURI' in token_id_info:
        erc721_token_id_detail['token_uri'] = token_id_info['tokenURI']

    return erc721_token_id_detail


def format_erc1155_token_id_detail(token_id_info):
    erc1155_token_id_detail = {
        'model': ERC1155TokenIdDetails,
        'address': to_normalized_address(token_id_info['address']),
        'token_id': token_id_info['token_id'],
        'token_supply': token_id_info['totalSupply'],
        'token_uri_info': None,
        'block_number': token_id_info['block_number'],
        'block_timestamp': token_id_info['block_timestamp'],
        'update_strategy': "EXCLUDED.block_number >= erc1155_token_id_details.block_number",
        'update_columns': ['token_supply', 'block_number', 'block_timestamp', 'update_time']
    }

    if 'tokenURI' in token_id_info:
        erc1155_token_id_detail['token_uri'] = token_id_info['uri']

    return erc1155_token_id_detail
