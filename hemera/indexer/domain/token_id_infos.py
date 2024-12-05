from dataclasses import dataclass
from typing import Optional

from hemera.common.utils.web3_utils import ZERO_ADDRESS
from hemera.indexer.domain import Domain


@dataclass
class ERC721TokenIdChange(Domain):
    token_address: str
    token_id: int
    token_owner: str
    block_number: int
    block_timestamp: int

    @staticmethod
    def from_token_dict(token_dict: dict):
        return ERC721TokenIdChange(
            token_address=token_dict["address"],
            token_id=token_dict["token_id"],
            token_owner=(token_dict["ownerOf"] if token_dict["ownerOf"] else ZERO_ADDRESS),
            block_number=token_dict["block_number"],
            block_timestamp=token_dict["block_timestamp"],
        )


@dataclass
class ERC721TokenIdDetail(Domain):
    token_address: str
    token_id: int
    token_uri: Optional[str]
    block_number: int
    block_timestamp: int
    token_uri_info: Optional[str] = None

    @staticmethod
    def from_token_dict(token_dict: dict):
        return ERC721TokenIdDetail(
            token_address=token_dict["address"],
            token_id=token_dict["token_id"],
            token_uri=token_dict["tokenURI"],
            block_number=token_dict["block_number"],
            block_timestamp=token_dict["block_timestamp"],
        )


@dataclass
class UpdateERC721TokenIdDetail(Domain):
    token_address: str
    token_id: int
    token_owner: str
    block_number: int
    block_timestamp: int

    @staticmethod
    def from_token_dict(token_dict: dict):
        return UpdateERC721TokenIdDetail(
            token_address=token_dict["address"],
            token_id=token_dict["token_id"],
            token_owner=(token_dict["ownerOf"] if token_dict["ownerOf"] else ZERO_ADDRESS),
            block_number=token_dict["block_number"],
            block_timestamp=token_dict["block_timestamp"],
        )


@dataclass
class ERC1155TokenIdDetail(Domain):
    token_address: str
    token_id: int
    token_uri: str
    block_number: int
    block_timestamp: int
    token_uri_info: Optional[str] = None

    @staticmethod
    def from_token_dict(token_dict: dict):
        return ERC1155TokenIdDetail(
            token_address=token_dict["address"],
            token_id=token_dict["token_id"],
            token_uri=token_dict["uri"],
            block_number=token_dict["block_number"],
            block_timestamp=token_dict["block_timestamp"],
        )


@dataclass
class UpdateERC1155TokenIdDetail(Domain):
    token_address: str
    token_id: int
    token_supply: int
    block_number: int
    block_timestamp: int

    @staticmethod
    def from_token_dict(token_dict: dict):
        return UpdateERC1155TokenIdDetail(
            token_address=token_dict["address"],
            token_id=token_dict["token_id"],
            token_supply=token_dict["totalSupply"],
            block_number=token_dict["block_number"],
            block_timestamp=token_dict["block_timestamp"],
        )
