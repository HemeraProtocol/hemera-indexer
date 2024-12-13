from dataclasses import dataclass
from typing import Any, Dict, Optional

from hemera.indexer.domains import Domain


@dataclass
class MorphDepositedTransactionOnL1(Domain):
    msg_hash: str
    version: Optional[int]
    index: Optional[int]
    l1_block_number: int
    l1_block_timestamp: int
    l1_block_hash: str
    l1_transaction_hash: str
    l1_from_address: str
    l1_to_address: str
    amount: int
    from_address: str
    to_address: str
    l1_token_address: str
    l2_token_address: str
    extra_info: Optional[Dict[str, Any]]
    _type: Optional[int]
    sender: Optional[str]
    target: Optional[str]
    data: Optional[str]


@dataclass
class MorphDepositedTransactionOnL2(Domain):
    msg_hash: str
    l2_block_number: int
    l2_block_timestamp: int
    l2_block_hash: str
    l2_transaction_hash: str
    l2_from_address: str
    l2_to_address: str


@dataclass
class MorphWithdrawalTransactionOnL1(Domain):
    msg_hash: str
    l1_block_number: int
    l1_block_timestamp: int
    l1_block_hash: str
    l1_transaction_hash: str
    l1_from_address: str
    l1_to_address: str


@dataclass
class MorphWithdrawalTransactionOnL2(Domain):
    msg_hash: str
    version: Optional[int]
    index: Optional[int]
    l2_block_number: int
    l2_block_timestamp: int
    l2_block_hash: str
    l2_transaction_hash: str
    l2_from_address: str
    l2_to_address: str
    amount: int
    from_address: str
    to_address: str
    l1_token_address: str
    l2_token_address: str
    extra_info: Optional[Dict[str, Any]]
    _type: Optional[int]
    sender: Optional[str]
    target: Optional[str]
    data: Optional[str]
