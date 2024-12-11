
from dataclasses import dataclass
from indexer.domain import FilterData


@dataclass
class VirtualsCreatedTokenD(FilterData):
    virtual_id: int
    token: str
    dao: str
    tba: str
    ve_token: str
    lp: str
    block_number: int