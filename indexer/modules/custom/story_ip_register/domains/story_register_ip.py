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

@dataclass
class StoryIpRegistered(Domain):
    transaction_hash: str
    log_index: int
    ip_account: str
    chain_id: int
    token_contract: str
    token_id: int
    contract_address: str
    block_number: int
    block_hash: str
    block_timestamp: int