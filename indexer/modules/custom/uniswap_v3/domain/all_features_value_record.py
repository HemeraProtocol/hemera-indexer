from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class AllFeatureValueRecord(FilterData):
    feature_id: int
    block_number: int
    address: str
    value: dict
