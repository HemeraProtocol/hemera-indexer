from dataclasses import dataclass

from indexer.domain import Domain


@dataclass
class AddressOpenseaTransaction(Domain):
    address: str
    related_address: str
    is_offer: bool
    transaction_type: int
    order_hash: str
    zone: str

    offer: dict
    consideration: dict

    fee: dict

    transaction_hash: str
    block_number: int
    log_index: int
    block_timestamp: int
    block_hash: str
