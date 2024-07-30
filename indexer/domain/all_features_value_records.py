from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class AllFeatureValueRecords(FilterData):
    feature_id: int
    block_number: int
    address: str
    value: str
