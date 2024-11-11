from dataclasses import dataclass

from indexer.domain import Domain


@dataclass
class EtherFiShareBalanceD(Domain):
    address: str
    token_address: str
    shares: int
    block_number: int


@dataclass
class EtherFiShareBalanceCurrentD(Domain):
    address: str
    token_address: str
    shares: int
    block_number: int


@dataclass
class EtherFiPositionValuesD(Domain):
    block_number: int
    total_share: int
    total_value_out_lp: int
    total_value_in_lp: int
