from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain


@dataclass
class UniswapV3Pools(Domain):
    nft_address: str
    pool_address: str
    token0_address: str
    token1_address: str
    fee: int
    tick_spacing: int
    mint_block_number: int
