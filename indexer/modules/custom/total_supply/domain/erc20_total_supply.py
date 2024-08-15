from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class Erc20TotalSupply(FilterData):
    token_address: str
    total_supply: int
    called_block_number: int
    called_block_timestamp: int
