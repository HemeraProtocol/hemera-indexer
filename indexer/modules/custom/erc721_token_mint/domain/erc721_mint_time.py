from dataclasses import dataclass
from indexer.domain import Domain, FilterData

@dataclass
class ERC721TokenMint(FilterData):
    token_address: str
    token_id: int
    block_number: int
    block_timestamp: int
    transaction_hash: str
