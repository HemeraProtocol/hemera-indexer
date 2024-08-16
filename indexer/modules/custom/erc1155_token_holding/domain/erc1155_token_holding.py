from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class Erc1155TokenHolding(FilterData):
    token_address: str
    wallet_address: str
    token_id: int
    balance: int
    called_block_number: int
    called_block_timestamp: int
