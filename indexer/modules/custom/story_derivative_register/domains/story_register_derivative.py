from dataclasses import dataclass
from typing import List

from indexer.domain import Domain, FilterData


@dataclass
class StoryDerivativeRegister(FilterData):
    log_index: int
    caller: str
    child_ip_id: str
    license_token_ids: List[int]
    parent_ip_ids: List[str]
    license_terms_ids: List[int]
    license_template: str
    contract_address: str
    transaction_hash: str
    block_number: int
    block_timestamp: int


@dataclass
class StoryDerivativeRegistered(Domain):
    transaction_hash: str
    log_index: int
    caller: str
    child_ip_id: str
    license_token_ids: List[int]
    parent_ip_ids: List[str]
    license_terms_ids : List[int]
    license_template: str
    contract_address: str
    block_number: int
    block_timestamp: int
