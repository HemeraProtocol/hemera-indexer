from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class StakedFBTCDetail(FilterData):
    contract_address: str
    protocol_id: str
    wallet_address: str
    amount: int
    changed_amount: int
    block_number: int
    block_timestamp: int


@dataclass
class StakedFBTCCurrentStatus(FilterData):
    contract_address: str
    protocol_id: str
    wallet_address: str
    amount: int
    changed_amount: int
    block_number: int
    block_timestamp: int


@dataclass
class TransferredFBTCDetail(FilterData):
    contract_address: str
    protocol_id: str
    wallet_address: str
    amount: int
    changed_amount: int
    block_number: int
    block_timestamp: int


@dataclass
class TransferredFBTCCurrentStatus(FilterData):
    contract_address: str
    protocol_id: str
    wallet_address: str
    amount: int
    changed_amount: int
    block_number: int
    block_timestamp: int
