from dataclasses import dataclass
from typing import Optional

from hemera.indexer.domains import Domain


@dataclass
class Token(Domain):
    address: str
    token_type: str
    name: Optional[str]
    symbol: Optional[str]
    decimals: Optional[int]
    block_number: int
    total_supply: Optional[int] = None


@dataclass
class UpdateToken(Domain):
    address: str
    block_number: int
    total_supply: Optional[int] = None


@dataclass
class MarkBalanceToken(Domain):
    address: str
    fail_balance_of_count: int
    no_balance_of: Optional[bool] = True


@dataclass
class MarkTotalSupplyToken(Domain):
    address: str
    fail_total_supply_count: int
    no_total_supply: Optional[bool] = True
