from dataclasses import dataclass

from indexer.domain import FilterData


# todo: 
@dataclass
class L1toL2TxOnL2(FilterData):
    srcOwner: str
    destOwner: str
    transaction_hash: str
    token_address: str
    srcChainId: int
    destChainId: int
    token_id: str
    amount: int
    fee: int
    block_number: int
    block_timestamp: int

@dataclass
class L2ToL1TxOnL2(FilterData):
    pass
