from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from indexer.domain import Domain


@dataclass
class ENSRegister(Domain):
    transaction_hash: str
    log_index: int
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    block_timestamp: Optional[datetime] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None

    expires: Optional[datetime] = None
    name: Optional[str] = None
    label: Optional[str] = None
    owner: Optional[str] = None
    base_node: Optional[str] = None
    node: Optional[str] = None
    event_name: Optional[str] = None


@dataclass
class ENSNameRenew(Domain):
    transaction_hash: str
    log_index: int
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    block_timestamp: Optional[datetime] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None

    name: Optional[str] = None
    node: Optional[str] = None
    label: Optional[str] = None
    expires: Optional[datetime] = None
    event_name: Optional[str] = None


@dataclass
class ENSAddressChange(Domain):
    transaction_hash: str
    log_index: int
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    block_timestamp: Optional[datetime] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None

    node: Optional[str] = None
    address: Optional[str] = None
    event_name: Optional[str] = None


@dataclass
class ENSNameChanged(Domain):
    transaction_hash: str
    log_index: int
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    block_timestamp: Optional[datetime] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None

    reverse_name: Optional[str] = None
    address: Optional[str] = None
    node: Optional[str] = None
    reverse_node: Optional[str] = None
    event_name: Optional[str] = None


@dataclass
class ENSRelDomain(Domain):

    node: Optional[str] = None
    token_id: Optional[str] = None
    owner: Optional[str] = None
    name: Optional[str] = None
    expires: Optional[datetime] = None
    address: Optional[str] = None
    reverse_name: Optional[str] = None
