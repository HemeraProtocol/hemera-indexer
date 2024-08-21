from dataclasses import dataclass

from indexer.domain import Domain, FilterData


@dataclass
class MerchantMoeErc1155TokenHolding(FilterData):
    token_address: str
    wallet_address: str
    token_id: int
    balance: int
    called_block_number: int
    called_block_timestamp: int


@dataclass
class MerchantMoeErc1155TokenCurrentHolding(FilterData):
    token_address: str
    wallet_address: str
    token_id: int
    balance: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoeErc1155TokenSupply(FilterData):
    token_address: str
    token_id: int
    total_supply: int
    called_block_number: int
    called_block_timestamp: int


@dataclass
class MerchantMoeErc1155TokenCurrentSupply(FilterData):
    token_address: str
    token_id: int
    total_supply: int
    block_number: int
    block_timestamp: int
