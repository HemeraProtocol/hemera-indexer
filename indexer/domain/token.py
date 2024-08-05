from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain


@dataclass
class Token(Domain):
    address: str
    token_type: str
    name: Optional[str]
    symbol: Optional[str]
    decimals: Optional[int]
    update_block_number: int
    total_supply: Optional[int] = None


@dataclass
class UpdateToken(Domain):
    address: str
    update_block_number: int
    total_supply: Optional[int] = None
