from dataclasses import dataclass
from datetime import datetime

from indexer.domain import FilterData


@dataclass
class InitCapitalPositionHistoryDomain(FilterData):
    position_id: int
    owner_address: str
    viewer_address: str
    mode: int

    collateral_pool_address: str
    collateral_token_addres: str
    collateral_amount: int

    borrow_pool_address: str
    borrow_token_address: str
    borrow_share: int
    borrow_amount: int

    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int


@dataclass
class InitCapitalPositionCreateDomain(FilterData):
    position_id: int
    owner_address: str
    viewer_address: str
    mode: int

    created_block_number: int
    created_block_timestamp: int
    created_transaction_hash: str
    created_log_index: int

    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int


@dataclass
class InitCapitalPositionUpdateDomain(FilterData):
    position_id: int
    owner_address: str
    viewer_address: str
    mode: int
    
    collateral_pool_address: str
    collateral_token_addres: str
    collateral_amount: int

    borrow_pool_address: str
    borrow_token_address: str
    borrow_share: int
    borrow_amount: int

    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int


@dataclass
class InitCapitalRecordDomain(FilterData):
    action_type: str
    position_id: int
    pool_address: str
    token_address: str
    amount: int
    share: int
    address: str

    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int