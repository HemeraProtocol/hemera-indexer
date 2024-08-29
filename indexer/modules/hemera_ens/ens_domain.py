from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from indexer.domain import Domain


"""for ens_middle"""

@dataclass
class ENSMiddleD(Domain):
    transaction_hash: str
    log_index: int
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    block_timestamp: Optional[datetime] = None
    method: Optional[str] = None
    event_name: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None

    base_node: Optional[str] = None  # 一级域名的NameHash 譬如 eth
    node: Optional[str] = None  # 完整域名的NameHash
    label: Optional[str] = None  # name的keccak-256
    name: Optional[str] = None
    expires: Optional[datetime] = None  # 过期时间
    owner: Optional[str] = None
    resolver: Optional[str] = None  # 解析器地址
    address: Optional[str] = None  # 该域名解析到的地址
    reverse_base_node: Optional[str] = None
    reverse_node: Optional[str] = None
    reverse_label: Optional[str] = None
    reverse_name: Optional[str] = None
    token_id: Optional[str] = None
    w_token_id: Optional[str] = None
    reorg: bool = False


"""below is for ens_record"""
@dataclass
class ENSRegisterD(Domain):

    expires: Optional[datetime] = None
    name: Optional[str] = None
    label: Optional[str] = None
    owner: Optional[str] = None
    base_node: Optional[str] = None
    node: Optional[str] = None
    token_id: Optional[str] = None
    w_token_id: Optional[str] = None


@dataclass
class ENSRegisterTokenD(Domain):
    node: Optional[str] = None
    token_id: Optional[str] = None


@dataclass
class ENSNameRenewD(Domain):

    node: Optional[str] = None
    expires: Optional[datetime] = None


@dataclass
class ENSAddressChangeD(Domain):

    node: Optional[str] = None
    address: Optional[str] = None


"""for ens_address"""
@dataclass
class ENSAddressD(Domain):

    address: Optional[str] = None
    reverse_node: Optional[str] = None
    name: Optional[str] = None


@dataclass
class ENSTokenTransferD(Domain):
    transaction_hash: str
    log_index: int
    from_address: str
    to_address: str
    token_id: int
    token_type: str
    token_address: str
    block_number: int
    block_hash: str
    block_timestamp: int