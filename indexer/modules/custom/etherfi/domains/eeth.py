from dataclasses import dataclass

from indexer.domain import Domain


@dataclass
class EtherFiShareBalance(Domain):
    address: str
    token_address: str
    shares: int
    block_number: int


@dataclass
class EtherFiPositionValues(Domain):
    block_number: int
    total_share: int
    total_value_out_lp: int
    total_value_in_lp: int
