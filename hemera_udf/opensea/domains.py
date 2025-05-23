from dataclasses import dataclass

from hemera.indexer.domains import Domain


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

    protocol_version: str = "1.6"


@dataclass
class OpenseaOrder(Domain):
    order_hash: str
    zone: str
    offerer: str
    recipient: str
    offer: dict
    consideration: dict
    block_timestamp: int
    block_hash: str
    transaction_hash: str
    log_index: int
    block_number: int

    protocol_version: str = "1.6"
