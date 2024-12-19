from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class UniswapV3Pool(Domain):
    position_token_address: str
    factory_address: str
    pool_address: str
    token0_address: str
    token1_address: str
    fee: int
    tick_spacing: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV3Token(Domain):
    position_token_address: str
    token_id: int
    pool_address: str
    tick_lower: int
    tick_upper: int
    fee: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV3PoolPrice(Domain):
    factory_address: str
    pool_address: str
    sqrt_price_x96: int
    tick: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV3TokenDetail(Domain):
    position_token_address: str
    token_id: int
    pool_address: str
    wallet_address: str
    liquidity: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV3PoolCurrentPrice(Domain):
    factory_address: str
    pool_address: str
    sqrt_price_x96: int
    tick: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV3SwapEvent(Domain):
    pool_address: str
    position_token_address: str
    transaction_from_address: str
    sender: str
    recipient: str
    amount0: int
    amount1: int
    liquidity: int
    tick: int
    sqrt_price_x96: int
    token0_address: str
    token1_address: str
    transaction_hash: str
    log_index: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV3TokenCurrentStatus(Domain):
    position_token_address: str
    token_id: int
    pool_address: str
    wallet_address: str
    liquidity: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV3TokenUpdateLiquidity(Domain):
    position_token_address: str
    token_id: int
    owner: str
    liquidity: int
    amount0: int
    amount1: int
    action_type: str
    transaction_hash: str
    pool_address: str
    token0_address: str
    token1_address: str
    log_index: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV3TokenCollectFee(Domain):
    position_token_address: str
    recipient: str
    owner: str
    token_id: int
    amount0: int
    amount1: int
    pool_address: str
    token0_address: str
    token1_address: str
    transaction_hash: str
    log_index: int
    block_number: int
    block_timestamp: int


@dataclass
class AgniV3Pool(UniswapV3Pool):
    pass


@dataclass
class AgniV3PoolFromTokenJob(UniswapV3Pool):
    pass


@dataclass
class AgniV3Token(UniswapV3Token):
    pass


@dataclass
class AgniV3PoolPrice(UniswapV3PoolPrice):
    pass


@dataclass
class AgniV3TokenDetail(UniswapV3TokenDetail):
    pass


@dataclass
class AgniV3PoolCurrentPrice(UniswapV3PoolCurrentPrice):
    pass


@dataclass
class AgniV3TokenCurrentStatus(UniswapV3TokenCurrentStatus):
    pass


@dataclass
class AgniV3SwapEvent(UniswapV3SwapEvent):
    pass


@dataclass
class AgniV3TokenUpdateLiquidity(UniswapV3TokenUpdateLiquidity):
    pass


@dataclass
class AgniV3TokenCollectFee(UniswapV3TokenCollectFee):
    pass


@dataclass
class UniswapV3PoolFromSwapEvent(UniswapV3Pool):
    pass


@dataclass
class UniswapV3PoolFromToken(UniswapV3Pool):
    pass


@dataclass
class TeahouseLiquidityHist(Domain):
    position_token_address: str
    pool_address: str
    liquidity: int
    tick_lower: int
    tick_upper: int
    block_number: int
    block_timestamp: int


@dataclass
class TeahouseLiquidityCurrent(Domain):
    position_token_address: str
    pool_address: str
    liquidity: int
    tick_lower: int
    tick_upper: int
    block_number: int
    block_timestamp: int
