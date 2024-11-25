from dataclasses import dataclass

from indexer.domain import FilterData


# todo: 
@dataclass
class L1toL2TxOnL2(FilterData):
    src_owner: str
    dest_owner: str
    transaction_hash: str
    token_address: str
    src_chain_id: int
    dest_chain_id: int
    token_id: str
    amount: int
    fee: int
    block_number: int
    block_timestamp: int

@dataclass
class L2toL1TxOnL2(FilterData):
    src_owner: str
    dest_owner: str
    transaction_hash: str
    token_address: str
    src_chain_id: int
    dest_chain_id: int
    token_id: str
    amount: int
    fee: int
    block_number: int
    block_timestamp: int
