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
    called_block_number: int


@dataclass
class UniswapV2PoolTotalSupply(FilterData):
    pool_address: str
    total_supply: int
    called_block_number: int
    called_block_timestamp: int


@dataclass
class UniswapV2PoolCurrentTotalSupply(FilterData):
    pool_address: str
    total_supply: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV2PoolReserves(FilterData):
    pool_address: str
    reserve0: int
    reserve1: int
    block_timestamp_last: int
    called_block_number: int
    called_block_timestamp: int


@dataclass
class UniswapV2PoolCurrentReserves(Domain):
    pool_address: str
    reserve0: int
    reserve1: int
    block_timestamp_last: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV2LiquidityHolding(FilterData):
    pool_address: str
    wallet_address: str
    balance: int
    called_block_number: int
    called_block_timestamp: int


@dataclass
class UniswapV2CurrentLiquidityHolding(Domain):
    pool_address: str
    wallet_address: str
    balance: int
    block_number: int
    block_timestamp: int
