from dataclasses import dataclass
from indexer.domain import Domain, FilterData
from typing import List

@dataclass
class StoryDerivativeRegister(FilterData):
    transaction_hash: str
    log_index: int
    caller: str
    child_ip_id: str
    license_token_ids: List[int]
    parent_ip_ids: List[str]
    license_terms_ids : List[int]
    license_template: str
    block_number: int
    block_timestamp: int