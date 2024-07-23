from dataclasses import dataclass, field
from typing import List

from indexer.domain import Domain


@dataclass
class Trace(Domain):
    trace_id: str
    from_address: str
    to_address: str
    value: int
    input: str
    output: str
    trace_type: str
    call_type: str
    gas: int
    gas_used: int
    subtraces: int
    error: str
    status: str
    block_number: int
    block_hash: str
    block_timestamp: int
    transaction_index: int
    transaction_hash: str
    trace_index: int
    trace_address: List[int] = field(default_factory=list)

    def __init__(self, trace_dict: dict):
        self.dict_to_entity(trace_dict)

    def is_contract_creation(self):
        return self.trace_type == 'create' or self.trace_type == 'create2'

    def is_transfer_value(self):
        status = self.value is not None and self.value > 0

        return status and self.from_address != self.to_address and self.trace_type != 'delegatecall'
