from dataclasses import dataclass
from typing import Optional

from indexer.domain import FilterData


@dataclass
class EigenLayerActionD(FilterData):
    transaction_hash: str
    log_index: int
    transaction_index: int
    block_number: Optional[int] = None
    block_timestamp: Optional[int] = None
    method: Optional[str] = None
    event_name: Optional[str] = None
    topic0: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None

    token: Optional[str] = None
    vault: Optional[str] = None
    amount: Optional[int] = None
    balance: Optional[int] = None
    staker: Optional[str] = None
    operator: Optional[str] = None
    withdrawer: Optional[str] = None
    shares: Optional[int] = None
    withdrawroot: Optional[str] = None


@dataclass
class KarakVaultTokenD(FilterData):
    vault: Optional[str] = None
    token: Optional[str] = None
    name: Optional[str] = None
    symbol: Optional[str] = None
    asset_type: Optional[int] = None


@dataclass
class EigenLayerAddressCurrentD(FilterData):
    address: Optional[str] = None
    vault: Optional[str] = None
    deposit_amount: Optional[int] = None
    start_withdraw_amount: Optional[int] = None
    finish_withdraw_amount: Optional[int] = None


def eigen_layer_address_current_factory():
    return EigenLayerAddressCurrentD(
        address=None,
        vault=None,
        deposit_amount=0,
        start_withdraw_amount=0,
        finish_withdraw_amount=0,
    )
