from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain


@dataclass
class Token(Domain):
    address: str
    token_type: str
    name: str
    symbol: str
    decimals: Optional[int]
    block_number: int
    total_supply: Optional[int] = None


@dataclass
class UpdateToken(Domain):
    address: str
    block_number: int
    total_supply: Optional[int] = None
