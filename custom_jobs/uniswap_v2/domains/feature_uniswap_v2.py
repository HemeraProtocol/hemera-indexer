from dataclasses import dataclass

from indexer.domains import FilterData


@dataclass
class UniswapV2Pool(FilterData):
    factory_address: str
    pool_address: str
    token0_address: str
    token1_address: str
    length: int
    called_block_number: int
