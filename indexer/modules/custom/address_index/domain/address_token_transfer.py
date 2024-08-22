from dataclasses import dataclass

from indexer.domain import Domain


@dataclass
class AddressTokenTransfer(Domain):
    address: str
    block_number: int
    log_index: int
    transaction_hash: str
    block_timestamp: int
    block_hash: str
    token_address: str
    related_address: str
    transfer_type: int
    value: int
