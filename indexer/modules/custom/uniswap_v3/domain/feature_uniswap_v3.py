from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class UniswapV3Pool(FilterData):
    nft_address: str
    pool_address: str
    token0_address: str
    token1_address: str
    fee: int
    tick_spacing: int
    called_block_number: int


@dataclass
class UniswapV3Token(FilterData):
    nft_address: str
    token_id: int
    pool_address: str
    tick_lower: int
    tick_upper: int
    fee: int
    called_block_number: int


@dataclass
class UniswapV3PoolPrice(FilterData):
    nft_address: str
    pool_address: str
    sqrt_price_x96: int
    called_block_number: int
    called_block_timestamp: int


@dataclass
class UniswapV3TokenDetail(FilterData):
    nft_address: str
    token_id: int
    pool_address: str
    wallet_address: str
    liquidity: int
    called_block_number: int
    called_block_timestamp: int


@dataclass
class UniswapV3PoolCurrentPrice(FilterData):
    nft_address: str
    pool_address: str
    sqrt_price_x96: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV3TokenCurrentStatus(FilterData):
    nft_address: str
    token_id: int
    pool_address: str
    wallet_address: str
    liquidity: int
    block_number: int
    block_timestamp: int
