from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain


@dataclass
class CurrentTraitsActiveness(Domain):
    block_number: int
    address: str
    value: dict
    update_time: Optional[int] = None

