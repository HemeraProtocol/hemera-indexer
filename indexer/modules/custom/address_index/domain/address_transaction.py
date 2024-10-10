from dataclasses import dataclass

from indexer.domain import Domain


@dataclass
class AddressTransaction(Domain):
    address: str
    block_number: int
    transaction_index: int
    transaction_hash: str
    block_timestamp: int
    block_hash: str
    txn_type: int
    related_address: str
    value: int
    transaction_fee: int
    receipt_status: int
    method: str
