from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class PendlePoolD(Domain):
    market_address: str
    sy_address: str
    pt_address: str
    yt_address: str
    underlying_asset: str
    block_number: int
    chain_id: int


@dataclass
class PendleUserActiveBalanceD(Domain):
    market_address: str
    user_address: str
    sy_balance: int
    active_balance: int
    total_active_supply: int
    market_sy_balance: int
    block_number: int
    chain_id: int


@dataclass
class PendleUserActiveBalanceCurrentD(Domain):
    market_address: str
    user_address: str
    sy_balance: int
    active_balance: int
    total_active_supply: int
    market_sy_balance: int
    block_number: int
    chain_id: int
