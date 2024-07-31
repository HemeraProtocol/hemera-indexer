from dataclasses import dataclass

from indexer.domain import Domain, FilterData
from typing import Optional


@dataclass
class UserOperationsResult(FilterData):
    user_op_hash: str
    sender: Optional[str]
    paymaster: Optional[str]
    nonce: Optional[float]
    status: Optional[bool]
    actual_gas_cost: Optional[float]
    actual_gas_used: Optional[int]
    init_code: Optional[str]
    call_data: Optional[str]
    call_gas_limit: Optional[int]
    verification_gas_limit: Optional[int]
    pre_verification_gas: Optional[int]
    max_fee_per_gas: Optional[int]
    max_priority_fee_per_gas: Optional[int]
    paymaster_and_data: Optional[str]
    signature: Optional[str]
    transactions_hash: Optional[str]
    transactions_index: Optional[int]
    block_number: Optional[int]
    block_timestamp: Optional[str]  # Consider using a datetime type if appropriate
    bundler: Optional[str]
    start_log_index: Optional[int]
    end_log_index: Optional[int]


