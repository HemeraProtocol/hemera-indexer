from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class DegenWallet:
    address: bytes
    token_address: bytes
    balance: float
    token_symbol: str
    token_decimals: int
    last_transaction_time: datetime
    total_value_usd: float
    block_number: int
    block_timestamp: datetime
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
