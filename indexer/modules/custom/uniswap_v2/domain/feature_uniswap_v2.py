from dataclasses import dataclass

from indexer.domain import FilterData


@dataclass
class UniswapV2Pool_(FilterData):
    factory_address: str
    pool_address: str
    token0_address: str
    token1_address: str
    length: int
    called_block_number: int


@dataclass
class UniswapV2Pool(FilterData):
    factory_address: str
    pool_address: str
    token0_address: str
    token1_address: str
    length: int
    block_number: int
    block_timestamp: int
