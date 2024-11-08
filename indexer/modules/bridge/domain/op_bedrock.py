from dataclasses import dataclass
from typing import Optional

from indexer.domain import FilterData


@dataclass
class OpL1ToL2DepositedTransaction(FilterData):
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
    extra_info: Optional[dict]
    _type: int
    sender: str
    target: str
    data: str


@dataclass
class OpL1ToL2DepositedTransactionOnL2(FilterData):
    msg_hash: str
    l2_block_number: int
    l2_block_timestamp: int
    l2_block_hash: str
    l2_transaction_hash: str
    l2_from_address: str
    l2_to_address: str


@dataclass
class OpL2ToL1WithdrawnTransactionFinalized(FilterData):
    msg_hash: str
    l1_block_number: int
    l1_block_timestamp: int
    l1_block_hash: str
    l1_transaction_hash: str
    l1_from_address: str
    l1_to_address: str


@dataclass
class OpL2ToL1WithdrawnTransactionOnL2(FilterData):
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
    extra_info: Optional[dict]
    _type: int
    sender: str
    target: str
    data: str


@dataclass
class OpL2ToL1WithdrawnTransactionProven(FilterData):
    msg_hash: str
    l1_proven_block_number: int
    l1_proven_block_timestamp: int
    l1_proven_block_hash: str
    l1_proven_transaction_hash: str
    l1_proven_from_address: str
    l1_proven_to_address: str


@dataclass
class OpStateBatch(FilterData):
    batch_index: int
    l1_block_number: int
    l1_block_timestamp: int
    l1_block_hash: str
    l1_transaction_hash: str
    batch_root: str
    end_block_number: int
    start_block_number: Optional[int] = None
    transaction_count: Optional[int] = None
