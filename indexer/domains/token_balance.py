from dataclasses import dataclass

from indexer.domains import Domain


@dataclass
class TokenBalance(Domain):
    address: str
    token_id: int
    token_type: str
    token_address: str
    balance: int
    block_number: int
    block_timestamp: int
