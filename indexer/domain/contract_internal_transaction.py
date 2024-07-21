from dataclasses import dataclass

from common.models.contract_internal_transactions import ContractInternalTransactions
from indexer.domain import Domain


@dataclass
class ContractInternalTransaction(Domain):
    trace_id: str
    from_address: str
    to_address: str
    value: int
    trace_type: str
    call_type: str
    gas: int
    gas_used: int
    trace_address: str
    error: str
    status: str
    block_number: int
    block_hash: str
    block_timestamp: int
    transaction_index: int
    transaction_hash: str
    trace_index: int

    def __init__(self, trace: dict):
        self.dict_to_entity(trace)
