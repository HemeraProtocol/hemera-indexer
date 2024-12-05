from dataclasses import dataclass

from hemera.indexer.domain import Domain


@dataclass
class TokenAddressNftInventory(Domain):
    token_address: str
    token_id: int
    wallet_address: str
