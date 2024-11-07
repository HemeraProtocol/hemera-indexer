from dataclasses import dataclass

from indexer.domain import Domain


@dataclass
class LidoShareBalance(Domain):
    address: str
    token_address: str
    shares: int
    block_number: int


@dataclass
class LidoPositionValues(Domain):
    block_number: int
    total_share: int
    buffered_eth: int
    consensus_layer: int
    deposited_validators: int
    cl_validators: int
