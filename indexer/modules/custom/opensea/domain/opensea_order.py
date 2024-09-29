from dataclasses import dataclass

from indexer.domain import Domain


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
