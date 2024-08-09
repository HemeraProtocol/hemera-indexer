from dataclasses import dataclass

from indexer.domain import Domain


@dataclass
class AddressNftTransfer(Domain):
    address: str
    block_number: int
    log_index: int
    transaction_hash: str
    block_timestamp: int
    block_hash: str
    token_address: str
    the_other_address: str
    transfer_type: int
    token_id: int
