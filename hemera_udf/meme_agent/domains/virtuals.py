from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class VirtualsCreatedTokenD(Domain):
    virtual_id: int
    token: str
    dao: str
    tba: str
    ve_token: str
    lp: str
    block_number: int
    block_timestamp: int
