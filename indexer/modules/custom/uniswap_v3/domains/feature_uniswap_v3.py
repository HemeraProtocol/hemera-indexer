from dataclasses import dataclass

from indexer.domain import FilterData


@dataclass
class UniswapV3Pool(FilterData):
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
class UniswapV3Token(FilterData):
    position_token_address: str
    token_id: int
    pool_address: str
    tick_lower: int
    tick_upper: int
    fee: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV3PoolPrice(FilterData):
    factory_address: str
    pool_address: str
    sqrt_price_x96: int
    tick: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV3TokenDetail(FilterData):
    position_token_address: str
    token_id: int
    pool_address: str
    wallet_address: str
    liquidity: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV3PoolCurrentPrice(FilterData):
    factory_address: str
    pool_address: str
    sqrt_price_x96: int
    tick: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV3SwapEvent(FilterData):
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
class UniswapV3TokenCurrentStatus(FilterData):
    position_token_address: str
    token_id: int
    pool_address: str
    wallet_address: str
    liquidity: int
    block_number: int
    block_timestamp: int


@dataclass
class UniswapV3TokenUpdateLiquidity(FilterData):
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
class UniswapV3TokenCollectFee(FilterData):
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
class IzumiPool(UniswapV3Pool):
    pool_id: int

@dataclass
class IzumiPoolId(FilterData):
    position_token_address: str
    pool_address: str
    pool_id: int


@dataclass
class IzumiToken(UniswapV3Token):
    pass


@dataclass
class IzumiPoolPrice(UniswapV3PoolPrice):
    pass


@dataclass
class IzumiTokenDetail(UniswapV3TokenDetail):
    pass


@dataclass
class IzumiPoolCurrentPrice(UniswapV3PoolCurrentPrice):
    pass


@dataclass
class IzumiTokenCurrentStatus(UniswapV3TokenCurrentStatus):
    pass


@dataclass
class IzumiSwapEvent(UniswapV3SwapEvent):
    pass


@dataclass
class IzumiTokenUpdateLiquidity(UniswapV3TokenUpdateLiquidity):
    pass


@dataclass
class IzumiTokenCollectFee(UniswapV3TokenCollectFee):
    pass
