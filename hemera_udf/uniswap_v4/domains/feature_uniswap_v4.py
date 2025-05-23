from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class UniswapV4Pool(Domain):
    position_token_address: str
    factory_address: str
    pool_address: str
    token0_address: str
    token1_address: str
    fee: int
    tick_spacing: int
    block_number: int
    block_timestamp: int
    hook_address: str


@dataclass
class UniswapV4PoolPrice(Domain):
    factory_address: str
    pool_address: str
    sqrt_price_x96: int
    tick: int
    token0_price: float
    token1_price: float
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV4PoolCurrentPrice(Domain):
    factory_address: str
    pool_address: str
    sqrt_price_x96: int
    tick: int
    token0_price: float
    token1_price: float
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV4SwapEvent(Domain):
    pool_address: str
    position_token_address: str
    transaction_from_address: str
    sender: str
    recipient: str
    amount0: int
    amount1: int
    token0_price: float
    token1_price: float
    amount_usd: float
    liquidity: int
    tick: int
    sqrt_price_x96: int
    token0_address: str
    token1_address: str
    transaction_hash: str
    log_index: int
    block_number: int
    block_timestamp: int
    hook_data: str = None  # JSON string of hook-related data


@dataclass
class UniswapV4Hook(Domain):
    hook_address: str
    factory_address: str
    pool_address: str
    hook_type: str  # e.g., "fee", "dynamic_fee", "limit_order", etc.
    hook_data: str  # JSON string of hook-specific data
    block_number: int
    block_timestamp: int
