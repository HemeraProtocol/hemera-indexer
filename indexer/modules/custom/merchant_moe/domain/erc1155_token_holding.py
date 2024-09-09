from dataclasses import dataclass

from indexer.domain import Domain, FilterData


@dataclass
class MerchantMoeErc1155TokenSupply(FilterData):
    token_address: str
    token_id: int
    total_supply: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoeErc1155TokenCurrentSupply(FilterData):
    token_address: str
    token_id: int
    total_supply: int
    block_number: int
    block_timestamp: int
