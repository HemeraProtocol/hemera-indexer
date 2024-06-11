from eth_utils import to_normalized_address, to_int

from exporters.jdbc.schema.erc1155_token_id_details import ERC1155TokenIdDetails
from exporters.jdbc.schema.erc721_token_id_changes import ERC721TokenIdChanges
from exporters.jdbc.schema.erc721_token_id_details import ERC721TokenIdDetails


def format_erc721_token_id_change(token_id_info):
    erc721_token_id_change = {
        'model': ERC721TokenIdChanges,
        'address': to_normalized_address(token_id_info['address']),
        'token_id': token_id_info['token_id'],
        'token_owner': token_id_info['ownerOf'],
        'block_number': to_int(hexstr=token_id_info['block_number']),
        'block_timestamp': to_int(hexstr=token_id_info['block_timestamp'])
    }
    return erc721_token_id_change


def format_erc721_token_id_detail(token_id_info):
    erc721_token_id_detail = {
        'model': ERC721TokenIdDetails,
        'address': to_normalized_address(token_id_info['address']),
        'token_id': token_id_info['token_id'],
        'token_owner': token_id_info['ownerOf'],
        'token_uri': token_id_info['tokenURI'],
        'token_uri_info': None,
        'block_number': to_int(hexstr=token_id_info['block_number']),
        'block_timestamp': to_int(hexstr=token_id_info['block_timestamp']),
        'update_strategy': "EXCLUDED.block_number >= erc721_token_id_details.block_number"
    }
    return erc721_token_id_detail


def format_erc1155_token_id_detail(token_id_info):
    erc1155_token_id_detail = {
        'model': ERC1155TokenIdDetails,
        'address': to_normalized_address(token_id_info['address']),
        'token_id': token_id_info['token_id'],
        'token_supply': token_id_info['totalSupply'],
        'token_uri': token_id_info['uri'],
        'token_uri_info': None,
        'block_number': to_int(hexstr=token_id_info['block_number']),
        'block_timestamp': to_int(hexstr=token_id_info['block_timestamp']),
        'update_strategy': "EXCLUDED.block_number >= erc1155_token_id_details.block_number"
    }
    return erc1155_token_id_detail
