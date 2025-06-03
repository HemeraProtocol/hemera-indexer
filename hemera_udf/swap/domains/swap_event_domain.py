from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class UniswapV2SwapEvent(Domain):
    project: str
    version: int

    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int
    pool_address: str
    transaction_from_address: str
    sender: str
    token0_address: str
    token1_address: str
    amount0: int
    amount1: int
    token0_price: float
    token1_price: float
    amount_usd: float

    # ----
    to_address: str
    amount0_in: int
    amount1_in: int
    amount0_out: int
    amount1_out: int


@dataclass
class UniswapV3SwapEvent(Domain):
    project: str
    version: int

    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int
    pool_address: str
    transaction_from_address: str
    sender: str
    token0_address: str
    token1_address: str
    amount0: int
    amount1: int
    token0_price: float
    token1_price: float
    amount_usd: float

    # ----
    recipient: str
    position_token_address: str
    liquidity: int
    tick: int
    sqrt_price_x96: int


@dataclass
class UniswapV4SwapEvent(Domain):
    project: str
    version: int

    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int
    pool_address: str
    transaction_from_address: str
    sender: str
    token0_address: str
    token1_address: str
    amount0: int
    amount1: int
    token0_price: float
    token1_price: float
    amount_usd: float

    # ----
    recipient: str
    position_token_address: str
    liquidity: int
    tick: int
    sqrt_price_x96: int
    hook_data: str = None  # JSON string of hook-related data


@dataclass
class FourMemeSwapEvent(Domain):
    project: str
    version: int

    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int
    pool_address: str
    transaction_from_address: str
    sender: str
    token0_address: str
    token1_address: str
    amount0: int
    amount1: int
    token0_price: float
    token1_price: float
    amount_usd: float

    # --
    price: int
    amount: int
    cost: int
    fee: int
    offers: int
    funds: int
    # Type of trade: 'buy' or 'sell'
    trade_type: str
