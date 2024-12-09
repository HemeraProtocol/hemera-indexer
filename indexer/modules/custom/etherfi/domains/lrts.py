from dataclasses import dataclass

from indexer.domain import Domain


@dataclass
class EtherFiLrtExchangeRateD(Domain):
    exchange_rate: int
    token_address: str
    block_number: int
