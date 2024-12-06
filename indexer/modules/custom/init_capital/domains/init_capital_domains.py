from dataclasses import dataclass
from datetime import datetime

from indexer.domain import FilterData


@dataclass
class InitCapitalPositionHistoryDomain(FilterData):
    position_id: int
    owner_address: str
    viewer_address: str
    mode: int

    collaterals: dict
    borrows: dict

    block_number: int
    block_timestamp: int


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


@dataclass
class InitCapitalPositionUpdateDomain(FilterData):
    position_id: int
    owner_address: str
    viewer_address: str
    mode: int

    collaterals: dict
    borrows: dict

    block_number: int
    block_timestamp: int


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


@dataclass
class InitCapitalPoolHistoryDomain(FilterData):

    pool_address: str
    token_address: str
    total_asset: int
    total_supply: int
    total_debt: int
    total_debt_share: int

    block_number: int
    block_timestamp: int


@dataclass
class InitCapitalPoolUpdateDomain(FilterData):

    pool_address: str
    total_asset: int
    total_supply: int
    total_debt: int
    total_debt_share: int

    block_number: int
    block_timestamp: int
