from dataclasses import dataclass

from indexer.domain import Domain


@dataclass
class AddressTokenHolder(Domain):
    address: str
    token_address: str
    balance_of: str
