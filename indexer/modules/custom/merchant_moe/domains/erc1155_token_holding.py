from dataclasses import dataclass

from indexer.domains import Domain, FilterData


@dataclass
class MerchantMoeErc1155TokenHolding(FilterData):
    position_token_address: str
    wallet_address: str
    token_id: int
    balance: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoeErc1155TokenCurrentHolding(FilterData):
    position_token_address: str
    wallet_address: str
    token_id: int
    balance: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoeErc1155TokenSupply(FilterData):
    position_token_address: str
    token_id: int
    total_supply: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoeErc1155TokenCurrentSupply(FilterData):
    position_token_address: str
    token_id: int
    total_supply: int
    block_number: int
    block_timestamp: int
