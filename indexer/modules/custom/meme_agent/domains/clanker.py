from dataclasses import dataclass

from indexer.domain import FilterData


@dataclass
class ClankerCreatedTokenD(FilterData):
    token_address: str
    lp_nft_id: int
    deployer: str
    fid: int
    name: str
    symbol: str
    supply: int
    locker_address: str
    cast_hash: str
    block_number: int
    block_timestamp: int
    version: int
