from dataclasses import dataclass
from typing import Optional


@dataclass
class DepositedTransaction:
    msg_hash: Optional[str] = None
    version: Optional[int] = None
    index: Optional[int] = None
    block_number: Optional[int] = None
    block_timestamp: Optional[int] = None
    block_hash: Optional[str] = None
    transaction_hash: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    local_token_address: Optional[str] = None
    remote_token_address: Optional[str] = None
    bridge_from_address: Optional[str] = None
    bridge_to_address: Optional[str] = None
    amount: Optional[int] = None
    extra_info: Optional[dict] = None
    _type: Optional[int] = 0
    sender: Optional[str] = None
    target: Optional[str] = None
    data: Optional[str] = None
