from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class UniswapV3Pools(FilterData):
    nft_address: str
    pool_address: str
    token0_address: str
    token1_address: str
    fee: int
    tick_spacing: int
    mint_block_number: int
