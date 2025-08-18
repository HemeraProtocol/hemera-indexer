from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class SpectraLpBalance(Domain):
    token0_address: str
    token1_address: str
    token0_balance: int
    token1_balance: int

    block_number: int
    block_timestamp: int

