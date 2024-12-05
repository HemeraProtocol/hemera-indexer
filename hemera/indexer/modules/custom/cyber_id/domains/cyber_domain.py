from dataclasses import dataclass
from datetime import datetime

from hemera.indexer.domain import FilterData


@dataclass
class CyberAddressD(FilterData):
    address: str
    reverse_node: str
    name: str
    block_number: int


@dataclass
class CyberIDRegisterD(FilterData):
    label: str
    token_id: int
    node: str
    cost: int
    block_number: int
    registration: datetime


@dataclass
class CyberAddressChangedD(FilterData):
    node: str
    address: str
    block_number: int
