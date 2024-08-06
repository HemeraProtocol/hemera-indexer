from dataclasses import dataclass

from indexer.domain import Domain


@dataclass
class CoinBalance(Domain):
    address: str
    balance: int
    block_number: int
    block_timestamp: int

    def __init__(self, coin_balance: dict):
        self.dict_to_entity(coin_balance)
