from dataclasses import dataclass

from indexer.domain import Domain


@dataclass
class TokenAddressNftInventory(Domain):
    token_address: str
    token_id: int
    wallet_address: str
