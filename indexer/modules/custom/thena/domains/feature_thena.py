from dataclasses import dataclass

from indexer.domain import FilterData


@dataclass
class ThenaLiquidityDomain(FilterData):
    pool_address: str
    liquidity: int
    block_number: int
    block_timestamp: int


@dataclass
class ThenaSharesDomain(FilterData):
    farming_address: str
    gamma_address: str
    wallet_address: str

    shares: int
    total_supply: int
    tick_lower: int
    tick_upper: int

    block_number: int
    block_timestamp: int
