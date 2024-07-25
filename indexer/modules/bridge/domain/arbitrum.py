from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class ArbitrumL1ToL2TransactionOnL1(FilterData):
    msg_hash: str
    index: int
    l1_block_number: int
    l1_block_timestamp: int
    l1_block_hash: str
    l1_transaction_hash: str
    l1_from_address: str
    l1_to_address: str
    l1_token_address: Optional[str]
    l2_token_address: Optional[str]
    from_address: str
    to_address: str
    amount: int
    extra_info: dict
    _type: int

@dataclass
class ArbitrumL2ToL1TransactionOnL1(FilterData):
    msg_hash: str
    l1_transaction_hash: str
    l1_block_number: int
    l1_block_timestamp: int
    l1_block_hash: str
    l1_from_address: str
    l1_to_address: str


@dataclass
class TicketCreatedData(FilterData):
    msg_hash: str
    transaction_hash: str
    block_number: int
    block_timestamp: int
    block_hash: str
    from_address: str
    to_address: str


@dataclass
class BridgeCallTriggeredData(FilterData):
    msg_hash: str
    l1_transaction_hash: str
    l1_block_number: int
    l1_block_timestamp: int
    l1_block_hash: str
    l1_from_address: str
    l1_to_address: str
    outbox: str
    to: str
    value: int
    data: str


@dataclass
class TransactionToken(FilterData):
    transaction_hash: str
    l1Token: str
    amount: int


@dataclass
class ArbitrumTransactionBatch(FilterData):
    batch_index: int
    l1_block_number: int
    l1_block_timestamp: int
    l1_block_hash: str
    l1_transaction_hash: str
    end_block_number: str
    start_block_number: str
    transaction_count: Optional[int]


@dataclass
class ArbitrumStateBatchConfirmed(FilterData):
    node_num: int
    block_hash: str
    send_root: str
    l1_block_number: int
    l1_block_timestamp: int
    l1_block_hash: str
    l1_transaction_hash: str
    end_block_number: Optional[int]
    start_block_number: Optional[int]
    transaction_count: Optional[int]


@dataclass
class ArbitrumStateBatchCreated(FilterData):
    node_num: int
    create_l1_block_number: int
    create_l1_block_timestamp: int
    create_l1_block_hash: str
    create_l1_transaction_hash: str
    parent_node_hash: str
    node_hash: str


@dataclass
class BridgeToken(FilterData):
    l1_token_address: str
    l2_token_address: str


@dataclass
class ArbitrumL2ToL1TransactionOnL2(FilterData):
    msg_hash: str
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
    l1_token_address: Optional[str]
    l2_token_address: Optional[str]
    extra_info: dict

@dataclass
class ArbitrumL1ToL2TransactionOnL2(FilterData):
    msg_hash: str
    l2_block_number: int
    l2_block_timestamp: int
    l2_block_hash: str
    l2_transaction_hash: str
    l2_from_address: str
    l2_to_address: str
