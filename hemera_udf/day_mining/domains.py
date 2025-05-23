from dataclasses import dataclass
from typing import Optional

from hemera.indexer.domains import Domain


@dataclass
class CurrentTraitsActiveness(Domain):
    block_number: int
    address: str
    value: dict
    update_time: Optional[int] = None
