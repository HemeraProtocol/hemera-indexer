from dataclasses import dataclass

from indexer.domain import FilterData


@dataclass
class LarryCreatedTokenD(FilterData):
    token: str
    party: str
    recipient: str
    name: str
    symbol: str
    eth_value: int
    block_number: int
    block_timestamp: int
