from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class UniswapV2Pool(FilterData):
    factory_address: str
    pool_address: str
    token0_address: str
    token1_address: str
    length: int
    mint_block_number: int
