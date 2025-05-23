from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class BlockTokenPrice(Domain):
    token_symbol: str
    token_price: float
    block_number: int


@dataclass
class DexBlockTokenPrice(Domain):
    token_address: str
    token_symbol: str
    decimals: int
    amount: float
    amount_usd: float
    token_price: float

    block_number: int
    block_timestamp: int


@dataclass
class DexBlockTokenPriceCurrent(Domain):
    token_address: str
    token_symbol: str
    decimals: int
    amount: float
    amount_usd: float
    token_price: float

    block_number: int
    block_timestamp: int
