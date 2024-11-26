from dataclasses import dataclass

from indexer.domains import Domain


@dataclass
class AddressContractOperation(Domain):
    address: str

    trace_from_address: str
    contract_address: str

    trace_id: str
    block_number: int
    transaction_index: int
    transaction_hash: str
    block_timestamp: int
    block_hash: str

    error: str
    status: int

    creation_code: str
    deployed_code: str

    gas: int
    gas_used: int

    trace_type: str
    call_type: str

    transaction_receipt_status: int
