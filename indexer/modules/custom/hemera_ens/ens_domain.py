from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from indexer.domain import Domain, FilterData

"""for ens_middle"""


@dataclass
class ENSMiddleD(FilterData):
    transaction_hash: str
    log_index: int
    transaction_index: int
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    block_timestamp: Optional[datetime] = None
    method: Optional[str] = None
    event_name: Optional[str] = None
    topic0: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None

    base_node: Optional[str] = None
    node: Optional[str] = None
    label: Optional[str] = None
    name: Optional[str] = None
    registration: Optional[datetime] = None
    expires: Optional[datetime] = None
    owner: Optional[str] = None
    resolver: Optional[str] = None
    address: Optional[str] = None
    reverse_base_node: Optional[str] = None
    reverse_node: Optional[str] = None
    reverse_label: Optional[str] = None
    reverse_name: Optional[str] = None
    # erc721
    token_id: Optional[str] = None
    # erc1155
    w_token_id: Optional[str] = None
    reorg: bool = False


"""below is for ens_record"""


@dataclass
class ENSRegisterD(FilterData):

    registration: Optional[datetime] = None
    expires: Optional[datetime] = None
    name: Optional[str] = None
    label: Optional[str] = None
    first_owned_by: Optional[str] = None
    base_node: Optional[str] = None
    node: Optional[str] = None
    token_id: Optional[str] = None
    w_token_id: Optional[str] = None


@dataclass
class ENSNameRenewD(FilterData):

    node: Optional[str] = None
    expires: Optional[datetime] = None


@dataclass
class ENSAddressChangeD(FilterData):

    node: Optional[str] = None
    address: Optional[str] = None


"""for ens_address"""


@dataclass
class ENSAddressD(FilterData):

    address: Optional[str] = None
    reverse_node: Optional[str] = None
    name: Optional[str] = None
    block_number: Optional[int] = None
