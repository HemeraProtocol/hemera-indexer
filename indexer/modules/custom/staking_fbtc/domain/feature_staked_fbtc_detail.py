from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class StakedFBTCDetail(FilterData):
    contract_address: str
    protocol_id: str
    wallet_address: str
    amount: int
    log_index: int
    block_number: int
    block_timestamp: int


@dataclass
class TransferedFBTCDetail(FilterData):
    contract_address: str
    protocol_id: str
    wallet_address: str
    amount: int
    log_index: int
    block_number: int
    block_timestamp: int
