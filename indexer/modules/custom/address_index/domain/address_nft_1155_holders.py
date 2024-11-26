from dataclasses import dataclass

from indexer.domains import Domain


@dataclass
class AddressNft1155Holder(Domain):
    address: str
    token_address: str
    token_id: int
    balance_of: str
