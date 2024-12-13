from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class IzumiPool(Domain):
    position_token_address: str
    factory_address: str
    pool_address: str
    token0_address: str
    token1_address: str
    fee: int
    point_delta: int
    block_number: int
    block_timestamp: int
    pool_id: int


# @dataclass
# class IzumiToken(Domain):
#     pass


@dataclass
class IzumiPoolPrice(Domain):
    factory_address: str
    pool_address: str
    sqrt_price_x96: int
    current_point: int
    liquidity: int
    liquidity_x: int
    block_number: int
    block_timestamp: int


@dataclass
class IzumiPoolCurrentPrice(Domain):
    factory_address: str
    pool_address: str
    sqrt_price_x96: int
    current_point: int
    liquidity: int
    liquidity_x: int
    block_number: int
    block_timestamp: int


@dataclass
class IzumiTokenState(Domain):
    position_token_address: str
    token_id: int
    pool_address: str
    pool_id: int
    wallet_address: str
    left_pt: int
    right_pt: int
    liquidity: int
    block_number: int
    block_timestamp: int


@dataclass
class IzumiTokenCurrentState(Domain):
    position_token_address: str
    token_id: int
    pool_address: str
    pool_id: int
    wallet_address: str
    left_pt: int
    right_pt: int
    liquidity: int
    block_number: int
    block_timestamp: int


@dataclass
class IzumiSwapEvent(Domain):
    pool_address: str
    position_token_address: str
    transaction_from_address: str
    sender: str
    recipient: str
    amount0: int
    amount1: int
    current_point: int
    token0_address: str
    token1_address: str
    fee: int
    sell_x_earn_y: bool
    transaction_hash: str
    log_index: int
    block_number: int
    block_timestamp: int


# @dataclass
# class IzumiTokenUpdateLiquidity(Domain):
#     pass


# @dataclass
# class IzumiTokenCollectFee(Domain):
#     pass
