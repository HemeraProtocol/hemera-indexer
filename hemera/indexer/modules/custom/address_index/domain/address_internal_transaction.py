from dataclasses import dataclass

from hemera.indexer.domain import Domain


@dataclass
class AddressInternalTransaction(Domain):
    address: str

    trace_id: str
    block_number: int
    transaction_index: int
    transaction_hash: str
    block_timestamp: int
    block_hash: str

    error: str
    status: int

    input_method: str

    value: int
    gas: int
    gas_used: int

    trace_type: str
    call_type: str

    txn_type: int
    related_address: str

    transaction_receipt_status: int
