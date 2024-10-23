from dataclasses import dataclass
from typing import Optional

from indexer.domain import FilterData


@dataclass
class AaveV2ReserveD(FilterData):
    asset: str
    a_token_address: str
    stable_debt_token_address: str
    variable_debt_token_address: str
    interest_rate_strategy_address: str
    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int


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
class AaveV2BaseRecord(FilterData):
    block_number: Optional[int] = None
    block_timestamp: Optional[int] = None
    transaction_hash: Optional[str] = None
    log_index: Optional[int] = None
    method: Optional[str] = None
    event_name: Optional[str] = None
    topic0: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None


@dataclass
class AaveV2DepositD(AaveV2BaseRecord):
    reserve: Optional[str] = None
    on_behalf_of: Optional[str] = None
    referral: Optional[int] = None
    user: Optional[str] = None
    amount: Optional[int] = None


@dataclass
class AaveV2WithdrawD(AaveV2BaseRecord):
    reserve: Optional[str] = None
    user: Optional[str] = None
    to: Optional[str] = None
    amount: Optional[int] = None


@dataclass
class AaveV2BorrowD(AaveV2BaseRecord):
    reserve: Optional[str] = None
    on_behalf_of: Optional[str] = None
    referral: Optional[int] = None
    user: Optional[str] = None
    amount: Optional[int] = None
    borrow_rate_mode: Optional[int] = None
    borrow_rate: Optional[int] = None


@dataclass
class AaveV2RepayD(AaveV2BaseRecord):
    reserve: Optional[str] = None
    user: Optional[str] = None
    repayer: Optional[str] = None
    amount: Optional[int] = None


@dataclass
class AaveV2FlashLoanD(AaveV2BaseRecord):
    target: Optional[str] = None
    # initiator -> user, use `user`
    user: Optional[str] = None
    reserve: Optional[str] = None
    amount: Optional[int] = None
    premium: Optional[int] = None
    referral: Optional[int] = None


@dataclass
class AaveV2LiquidationCallD(AaveV2BaseRecord):
    collateral_asset: Optional[str] = None
    debt_asset: Optional[str] = None
    user: Optional[str] = None
    debt_to_cover: Optional[int] = None
    liquidated_collateral_amount: Optional[int] = None
    liquidator: Optional[str] = None
    receive_atoken: Optional[str] = None


@dataclass
class AaveV2AddressCurrentD(FilterData):
    address: Optional[str] = None
    asset: Optional[str] = None
    supply_amount: Optional[int] = None
    borrow_amount: Optional[int] = None
    block_number: Optional[int] = None
    block_timestamp: Optional[int] = None
    total_value_of_liquidation: Optional[int] = None
    liquidation_time: Optional[int] = None


def aave_v2_address_current_factory():
    return AaveV2AddressCurrentD(
        address=None,
        asset=None,
        supply_amount=0,
        borrow_amount=0,
        block_timestamp=None,
        block_number=None,
        total_value_of_liquidation=None,
        liquidation_time=None,
    )
