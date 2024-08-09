import datetime
from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class BlueChipHolder(FilterData):
    wallet_address: str
    hold_detail: dict
    current_count: int
    called_block_number: int
    called_block_timestamp: int
