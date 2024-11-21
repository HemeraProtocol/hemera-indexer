from dataclasses import dataclass

from indexer.domain import FilterData


@dataclass
class PendlePoolD(FilterData):
    market_address: str
    sy_address: str
    pt_address: str
    yt_address: str
    block_number: int
    chain_id: int
