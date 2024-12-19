from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class UniswapV2Pool(Domain):
    factory_address: str
    pool_address: str
    token0_address: str
    token1_address: str
    length: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV2SwapEvent(Domain):
    sender: str
    amount0_in: int
    amount1_in: int
    amount0_out: int
    amount1_out: int
    log_index: int
    to_address: str
    pool_address: str
    block_number: int
    block_timestamp: int
    transaction_hash: str


@dataclass
class UniswapV2Erc20TotalSupply(Domain):
    token_address: str
    total_supply: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV2Erc20CurrentTotalSupply(Domain):
    token_address: str
    total_supply: int
    block_number: int
    block_timestamp: int
