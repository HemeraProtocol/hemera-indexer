import datetime
from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class BlueChipHolder(FilterData):
    wallet_address: str
    hold_detail: dict
    current_count: int
    block_number: int
    block_timestamp: int
