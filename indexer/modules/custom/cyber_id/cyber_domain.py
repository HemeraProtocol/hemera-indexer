from dataclasses import dataclass
from typing import Optional

from indexer.domain import FilterData


@dataclass
class CyberAddressD(FilterData):

    address: Optional[str] = None
    reverse_node: Optional[str] = None
    name: Optional[str] = None
    block_number: Optional[int] = None
