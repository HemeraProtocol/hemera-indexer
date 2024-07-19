from dataclasses import dataclass
from typing import Tuple

from indexer.domain import Domain


@dataclass
class BlockTsMapper(Domain):
    block_number: int
    timestamp: int

    def __init__(self, mapper: Tuple[int, int]):
        self.block_number = mapper[1]
        self.timestamp = mapper[0]
