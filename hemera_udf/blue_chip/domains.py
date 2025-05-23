from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class BlueChipHolder(Domain):
    wallet_address: str
    hold_detail: dict
    current_count: int
    called_block_number: int
    called_block_timestamp: int
