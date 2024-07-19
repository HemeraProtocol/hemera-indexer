from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain


@dataclass
class ERC721TokenIdChange(Domain):
    address: str
    token_id: int
    token_owner: str
    block_number: int
    block_timestamp: int

    def __init__(self, token_dict: dict):
        self.address = token_dict['address']
        self.token_id = token_dict['token_id']
        self.token_owner = token_dict['ownerOf']
        self.block_number = token_dict['block_number']
        self.block_timestamp = token_dict['block_timestamp']


@dataclass
class ERC721TokenIdDetail(Domain):
    address: str
    token_id: int
    token_owner: str
    token_uri: str
    block_number: int
    block_timestamp: int
    token_uri_info: Optional[str] = None

    def __init__(self, token_dict: dict):
        self.address = token_dict['address']
        self.token_id = token_dict['token_id']
        self.token_owner = token_dict['ownerOf']
        self.token_uri = token_dict['tokenURI']
        self.block_number = token_dict['block_number']
        self.block_timestamp = token_dict['block_timestamp']


@dataclass
class UpdateERC721TokenIdDetail(Domain):
    address: str
    token_id: int
    token_owner: str
    block_number: int
    block_timestamp: int

    def __init__(self, token_dict: dict):
        self.address = token_dict['address']
        self.token_id = token_dict['token_id']
        self.token_owner = token_dict['ownerOf']
        self.block_number = token_dict['block_number']
        self.block_timestamp = token_dict['block_timestamp']


@dataclass
class ERC1155TokenIdDetail(Domain):
    address: str
    token_id: int
    token_supply: int
    token_uri: str
    block_number: int
    block_timestamp: int
    token_uri_info: Optional[str] = None

    def __init__(self, token_dict: dict):
        self.address = token_dict['address']
        self.token_id = token_dict['token_id']
        self.token_supply = token_dict['totalSupply']
        self.token_uri = token_dict['uri']
        self.block_number = token_dict['block_number']
        self.block_timestamp = token_dict['block_timestamp']


class UpdateERC1155TokenIdDetail(Domain):
    address: str
    token_id: int
    token_supply: int
    block_number: int
    block_timestamp: int

    def __init__(self, token_dict: dict):
        self.address = token_dict['address']
        self.token_id = token_dict['token_id']
        self.token_supply = token_dict['totalSupply']
        self.block_number = token_dict['block_number']
        self.block_timestamp = token_dict['block_timestamp']
