from dataclasses import dataclass

from indexer.domain import FilterData


# todo: 
@dataclass
class L1ToL2(FilterData):
    token_id: int
    amount: int
    sender: str
    srcChainId:int
    srcOwner: str
    destChainId:int
    destOwner: str
    transaction_hash: str
    fee: int
    block_number: int
    block_timestamp: int

@dataclass
class L2ToL1(FilterData):
    pass
