from dataclasses import dataclass
from typing import Optional

from indexer.domain import FilterData


@dataclass
class AaveV1ReserveD(FilterData):
    asset: str
    asset_decimals: Optional[int]
    asset_symbol: Optional[str]
    a_token_address: str
    a_token_symbol: Optional[str]
    a_token_decimals: Optional[int]

    interest_rate_strategy_address: str
    block_number: int
    block_timestamp: int
    transaction_hash: str
    log_index: int
    topic0: Optional[str] = None
    event_name: Optional[str] = None


@dataclass
class AaveV1BaseRecord(FilterData):
    block_number: Optional[int] = None
    block_timestamp: Optional[int] = None
    transaction_hash: Optional[str] = None
    log_index: Optional[int] = None
    event_name: Optional[str] = None
    topic0: Optional[str] = None


@dataclass
class AaveV1DepositD(AaveV1BaseRecord):
    reserve: Optional[str] = None
    referral: Optional[int] = None
    aave_user: Optional[str] = None
    amount: Optional[int] = None


@dataclass
class AaveV1WithdrawD(AaveV1BaseRecord):
    reserve: Optional[str] = None
    aave_user: Optional[str] = None
    to_address: Optional[str] = None
    amount: Optional[int] = None


@dataclass
class AaveV1BorrowD(AaveV1BaseRecord):
    reserve: Optional[str] = None
    referral: Optional[int] = None
    aave_user: Optional[str] = None
    amount: Optional[int] = None
    borrow_rate_mode: Optional[int] = None
    borrow_rate: Optional[int] = None


@dataclass
class AaveV1RepayD(AaveV1BaseRecord):
    reserve: Optional[str] = None
    aave_user: Optional[str] = None
    repayer: Optional[str] = None
    amount: Optional[int] = None
    borrow_rate_mode: Optional[int] = None
    # debt, after repayed
    after_repay_debt: Optional[int] = None


@dataclass
class AaveV1FlashLoanD(AaveV1BaseRecord):
    target: Optional[str] = None
    # initiator -> user, use `aave_user`
    aave_user: Optional[str] = None
    reserve: Optional[str] = None
    amount: Optional[int] = None
    premium: Optional[int] = None
    referral: Optional[int] = None


@dataclass
class AaveV1LiquidationCallD(AaveV1BaseRecord):
    collateral_asset: Optional[str] = None
    debt_asset: Optional[str] = None
    aave_user: Optional[str] = None
    debt_to_cover: Optional[int] = None
    liquidated_collateral_amount: Optional[int] = None
    liquidator: Optional[str] = None
    receive_atoken: Optional[str] = None
    debt_after_liquidation: Optional[int] = None
    collateral_after_liquidation: Optional[int] = None


@dataclass
class AaveV1AddressCurrentD(FilterData):
    address: Optional[str] = None
    asset: Optional[str] = None
    supply_amount: Optional[int] = None
    borrow_amount: Optional[int] = None
    borrow_rate_mode: Optional[int] = None
    block_number: Optional[int] = None
    block_timestamp: Optional[int] = None


@dataclass
class AaveV1LiquidationAddressCurrentD(FilterData):
    address: Optional[str] = None
    asset: Optional[str] = None
    last_total_value_of_liquidation: Optional[int] = None
    last_liquidation_time: Optional[int] = None
    block_number: Optional[int] = None


def aave_v1_address_current_factory():
    return AaveV1AddressCurrentD(
        address=None, asset=None, supply_amount=0, borrow_amount=0, block_timestamp=None, block_number=None
    )


@dataclass
class AaveV1CallRecordsD(FilterData):
    target: Optional[str] = None
    params: Optional[str] = None
    function: Optional[str] = None
    block_number: Optional[int] = None
    result: Optional[str] = None


@dataclass
class AaveV1ReserveDataD(FilterData):
    block_timestamp: Optional[int] = None
    transaction_hash: Optional[str] = None
    log_index: Optional[int] = None
    topic0: Optional[str] = None
    event_name: Optional[str] = None
    asset: Optional[str] = None
    liquidity_rate: Optional[int] = None
    stable_borrow_rate: Optional[int] = None
    variable_borrow_rate: Optional[int] = None
    liquidity_index: Optional[int] = None
    variable_borrow_index: Optional[int] = None
    block_number: Optional[int] = None


@dataclass
class AaveV1ReserveDataCurrentD(FilterData):
    asset: Optional[str] = None
    block_number: Optional[int] = None
    liquidity_rate: Optional[int] = None
    stable_borrow_rate: Optional[int] = None
    variable_borrow_rate: Optional[int] = None
    liquidity_index: Optional[int] = None
    variable_borrow_index: Optional[int] = None
