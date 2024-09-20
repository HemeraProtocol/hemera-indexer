from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from indexer.domain import FilterData, Domain


@dataclass
class KarakActionD(FilterData):
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

    vault: Optional[str] = None
    amount: Optional[int] = None
    minSharesOut: Optional[int] = None
    shares: Optional[int] = None
    withdrawer: Optional[str] = None
    staker: Optional[str] = None
    delegatedTo: Optional[str] = None
    nonce: Optional[int] = None
    start: Optional[int] = None
    request: Optional[str] = None


@dataclass
class KarakVaultTokenD(FilterData):
    vault: Optional[str] = None
    token: Optional[str] = None
    name: Optional[str] = None
    symbol: Optional[str] = None
    asset_type: Optional[int] = None


@dataclass
class KarakDepositD(FilterData):
    position_token_address: str
    factory_address: str
    pool_address: str
    token0_address: str
    token1_address: str
    fee: int
    tick_spacing: int
    block_number: int
    block_timestamp: int


@dataclass
class KarakStatWithdrawD(FilterData):
    pass


@dataclass
class KarakFinishWithDrawD(FilterData):
    pass
