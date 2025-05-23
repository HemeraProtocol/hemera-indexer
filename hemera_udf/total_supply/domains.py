from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class Erc20TotalSupply(Domain):
    token_address: str
    total_supply: int
    block_number: int
    block_timestamp: int


@dataclass
class Erc20CurrentTotalSupply(Domain):
    token_address: str
    total_supply: int
    block_number: int
    block_timestamp: int
