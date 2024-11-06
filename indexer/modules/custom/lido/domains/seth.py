from dataclasses import dataclass

from indexer.domain import Domain


@dataclass
class LidoShareBalance(Domain):
    address: str
    token_address: str
    balance: int
    block_number: int
    block_timestamp: int


@dataclass
class LidoPositionBalance(Domain):
    block_number: int
    total_share: int
    buffered_eth: int
    consensus_layer: int
    deposited_validators: int
    cl_validators: int
