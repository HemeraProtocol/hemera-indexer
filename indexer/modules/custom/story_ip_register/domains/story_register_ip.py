from dataclasses import dataclass

from indexer.domain import Domain, FilterData


@dataclass
class StoryIpRegister(FilterData):
    ip_account: str
    nft_contract: str
    nft_id: int
    chain_id: int
    block_number: int
    contract_address: str
    transaction_hash: str
