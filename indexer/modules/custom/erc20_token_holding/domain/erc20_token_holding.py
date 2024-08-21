from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class Erc20TokenHolding(FilterData):
    token_address: str
    wallet_address: str
    balance: int
    called_block_number: int
    called_block_timestamp: int


@dataclass
class Erc20CurrentTokenHolding(Domain):
    token_address: str
    wallet_address: str
    balance: int
    block_number: int
    block_timestamp: int
