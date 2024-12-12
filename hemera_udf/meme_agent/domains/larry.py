from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class LarryCreatedTokenD(Domain):
    token: str
    party: str
    recipient: str
    name: str
    symbol: str
    eth_value: int
    block_number: int
    block_timestamp: int
