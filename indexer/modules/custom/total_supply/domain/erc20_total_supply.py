from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class Erc20TotalSupply(FilterData):
    token_address: str
    total_supply: int
    block_number: int
    block_timestamp: int


@dataclass
class Erc20CurrentTotalSupply(FilterData):
    token_address: str
    total_supply: int
    block_number: int
    block_timestamp: int
