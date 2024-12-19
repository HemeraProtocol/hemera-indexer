from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class InitCapitalPositionHistoryDomain(Domain):
    position_id: int
    owner_address: str
    viewer_address: str
    mode: int

    collaterals: dict
    borrows: dict

    block_number: int
    block_timestamp: int


@dataclass
class InitCapitalPositionCreateDomain(Domain):
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
class InitCapitalPositionUpdateDomain(Domain):
    position_id: int
    owner_address: str
    viewer_address: str
    mode: int

    collaterals: dict
    borrows: dict

    block_number: int
    block_timestamp: int


@dataclass
class InitCapitalRecordDomain(Domain):
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
class InitCapitalPoolHistoryDomain(Domain):

    pool_address: str
    token_address: str
    total_asset: int
    total_supply: int
    total_debt: int
    total_debt_share: int

    block_number: int
    block_timestamp: int


@dataclass
class InitCapitalPoolUpdateDomain(Domain):

    pool_address: str
    total_asset: int
    total_supply: int
    total_debt: int
    total_debt_share: int

    block_number: int
    block_timestamp: int
