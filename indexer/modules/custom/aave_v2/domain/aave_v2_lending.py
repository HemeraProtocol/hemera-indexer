from dataclasses import dataclass
from typing import Optional

from indexer.domain import Domain, FilterData


@dataclass
class AaveV2LendingPool(FilterData):
    asset_address: str
    a_token_address: str
    stable_debt_token_address: str
    variable_debt_token_address: str
    interest_rate_strategy_address: str
    block_number: int
    block_timestamp: int


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
