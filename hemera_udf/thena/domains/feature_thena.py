from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class ThenaLiquidityDomain(Domain):
    pool_address: str
    liquidity: int
    block_number: int
    block_timestamp: int


@dataclass
class ThenaSharesDomain(Domain):
    farming_address: str
    gamma_address: str
    pool_address: str
    wallet_address: str

    shares: int
    total_supply: int
    tick_lower: int
    tick_upper: int

    block_number: int
    block_timestamp: int
