from dataclasses import dataclass

from indexer.domain import Domain


@dataclass
class CurrentTokenBalance(Domain):
    address: str
    token_id: int
    token_type: str
    token_address: str
    balance: int
    block_number: int
    block_timestamp: int
