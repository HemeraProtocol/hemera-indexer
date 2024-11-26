from dataclasses import dataclass

from indexer.domains import Domain


@dataclass
class AddressTokenHolder(Domain):
    address: str
    token_address: str
    balance_of: str
