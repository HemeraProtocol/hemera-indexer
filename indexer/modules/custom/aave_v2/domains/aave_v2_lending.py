from dataclasses import dataclass
from typing import Optional

from indexer.domain import FilterData


@dataclass
class AaveV2LendingPool(FilterData):
    reverse: str
    a_token_address: str
    stable_debt_token_address: str
    variable_debt_token_address: str
    interest_rate_strategy_address: str
    block_number: int
    block_timestamp: int


@dataclass
class ReserveDataUpdatedD(FilterData):
    reserve: str
    liquidityRate: int
    stableBorrowRate: int
    variableBorrowRate: int
    liquidityIndex: int
    variableBorrowIndex: int


@dataclass
class AaveV2LendingPoolReserveFactorCurrent(FilterData):
    asset_address: str
    factor: int
    block_number: int
    block_timestamp: int


@dataclass
class AaveV2LendingPoolReserveFactorRecord(FilterData):
    asset_address: str
    factor: int
    block_number: int
    block_timestamp: int


@dataclass
class AaveV2DepositD(FilterData):
    reserve: Optional[str] = None
    onBehalfOf: Optional[str] = None
    referral: Optional[int] = None
    user: Optional[str] = None
    amount: Optional[int] = None

    block_number: Optional[int] = None
    block_timestamp: Optional[int] = None
    transaction_hash: Optional[str] = None
    log_index: Optional[int] = None


@dataclass
class AaveV2WithdrawD(FilterData):
    reserve: Optional[str] = None
    user: Optional[str] = None
    to: Optional[str] = None
    amount: Optional[int] = None

    block_number: Optional[int] = None
    block_timestamp: Optional[int] = None
    transaction_hash: Optional[str] = None
    log_index: Optional[int] = None


@dataclass
class AaveV2BorrowD(FilterData):
    reserve: Optional[str] = None
    onBehalfOf: Optional[str] = None
    referral: Optional[int] = None
    user: Optional[str] = None
    amount: Optional[int] = None
    borrow_rate_mode: Optional[int] = None
    borrow_rate: Optional[int] = None

    block_number: Optional[int] = None
    block_timestamp: Optional[int] = None
    transaction_hash: Optional[str] = None
    log_index: Optional[int] = None


@dataclass
class AaveV2RepayD(FilterData):
    reserve: Optional[str] = None
    user: Optional[str] = None
    repayer: Optional[str] = None
    amount: Optional[int] = None

    block_number: Optional[int] = None
    block_timestamp: Optional[int] = None
    transaction_hash: Optional[str] = None
    log_index: Optional[int] = None
