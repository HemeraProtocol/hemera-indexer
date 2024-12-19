from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class ClankerCreatedTokenD(Domain):
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
