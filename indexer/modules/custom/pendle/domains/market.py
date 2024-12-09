from dataclasses import dataclass

from indexer.domain import FilterData


@dataclass
class PendlePoolD(FilterData):
    market_address: str
    sy_address: str
    pt_address: str
    yt_address: str
    underlying_asset: str
    block_number: int
    chain_id: int


@dataclass
class PendleUserActiveBalanceD(FilterData):
    market_address: str
    user_address: str
    sy_balance: int
    active_balance: int
    total_active_supply: int
    market_sy_balance: int
    block_number: int
    chain_id: int


@dataclass
class PendleUserActiveBalanceCurrentD(FilterData):
    market_address: str
    user_address: str
    sy_balance: int
    active_balance: int
    total_active_supply: int
    market_sy_balance: int
    block_number: int
    chain_id: int
