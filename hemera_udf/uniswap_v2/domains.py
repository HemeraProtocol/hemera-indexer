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
    project: str
    version: int

    sender: str
    transaction_from_address: str
    pool_address: str
    token0_address: str
    token1_address: str
    amount0: int
    amount1: int
    token0_price: float
    token1_price: float
    amount_usd: float
    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int
    # ----
    to_address: str
    amount0_in: int
    amount1_in: int
    amount0_out: int
    amount1_out: int


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


@dataclass
class UniswapV2PoolFromSwapEvent(UniswapV2Pool):
    pass
