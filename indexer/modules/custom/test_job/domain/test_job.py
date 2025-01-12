from dataclasses import dataclass
from indexer.domain import FilterData

@dataclass
class TestUdfDomain(FilterData):
    from_address: str
    to_address: str
    value: int
    token_address: str
    block_timestamp: int
    block_number: int
    transaction_hash: str
    log_index: int
