from dataclasses import dataclass

from indexer.domain import Domain, FilterData


@dataclass
class MerChantMoeTokenBin(FilterData):
    token_address: str
    token_id: int
    reserve0_bin: int
    reserve1_bin: int
    block_number: int
    block_timestamp: int


@dataclass
class MerChantMoeTokenCurrentBin(FilterData):
    token_address: str
    token_id: int
    reserve0_bin: int
    reserve1_bin: int
    block_number: int
    block_timestamp: int


@dataclass
class MerChantMoePool(FilterData):
    token_address: str
    token0_address: str
    token1_address: str
    block_number: int
    block_timestamp: int
