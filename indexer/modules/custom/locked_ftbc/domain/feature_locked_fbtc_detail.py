from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class LockedFBTCDetail(FilterData):
    contract_address: str
    wallet_address: str
    minter: str
    received_amount: int
    fee: int
    log_index: int
    block_number: int
    block_timestamp: int
