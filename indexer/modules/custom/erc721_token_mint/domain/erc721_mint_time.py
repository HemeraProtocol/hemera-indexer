from dataclasses import dataclass
from indexer.domain import Domain, FilterData

@dataclass
class ERC721TokenMint(FilterData):
    ip_account: str
    nft_contract: str
    nft_id: int
    chain_id: int
    block_number: int
    transaction_hash: str
