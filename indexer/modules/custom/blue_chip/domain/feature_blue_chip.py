from dataclasses import dataclass

from indexer.domain import FilterData


@dataclass
class BlueChipHolder(FilterData):
    wallet_address: str
    hold_detail: dict
    current_count: int
    called_block_number: int
    called_block_timestamp: int
