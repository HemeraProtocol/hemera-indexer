from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain


@dataclass
class AllFeatureValueRecords(Domain):
    feature_id: int
    block_number: int
    address: str
    value: str
