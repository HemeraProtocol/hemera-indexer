from dataclasses import dataclass
from typing import Optional

from hemera.indexer.domain import Domain


@dataclass
class EigenLayerAction(Domain):
    transaction_hash: str
    log_index: int
    transaction_index: int
    internal_idx: Optional[int] = 0
    block_number: Optional[int] = None
    block_timestamp: Optional[int] = None
    event_name: Optional[str] = None

    token: Optional[str] = None
    strategy: Optional[str] = None
    staker: Optional[str] = None
    shares: Optional[int] = None
    withdrawer: Optional[str] = None
    withdrawroot: Optional[str] = None


@dataclass
class EigenLayerAddressCurrent(Domain):
    address: Optional[str] = None
    strategy: Optional[str] = None
    token: Optional[str] = None
    deposit_amount: Optional[int] = None
    start_withdraw_amount: Optional[int] = None
    finish_withdraw_amount: Optional[int] = None


def eigen_layer_address_current_factory():
    return EigenLayerAddressCurrent(
        address=None,
        strategy=None,
        token=None,
        deposit_amount=0,
        start_withdraw_amount=0,
        finish_withdraw_amount=0,
    )
