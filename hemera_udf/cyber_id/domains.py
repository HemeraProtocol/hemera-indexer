from dataclasses import dataclass
from datetime import datetime

from hemera.indexer.domains import Domain


@dataclass
class CyberAddressD(Domain):
    address: str
    reverse_node: str
    name: str
    block_number: int


@dataclass
class CyberIDRegisterD(Domain):
    label: str
    token_id: int
    node: str
    cost: int
    block_number: int
    registration: datetime


@dataclass
class CyberAddressChangedD(Domain):
    node: str
    address: str
    block_number: int
