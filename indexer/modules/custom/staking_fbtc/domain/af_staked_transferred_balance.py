from dataclasses import dataclass

from indexer.domain import FilterData


# records for all token
@dataclass
class AfStakedTransferredBalanceHistDomain(FilterData):
    contract_address: str
    protocol_id: str
    wallet_address: str
    token_address: str
    block_transfer_value: int
    block_cumulative_value: int
    block_number: int
    block_timestamp: int


@dataclass
class AfStakedTransferredBalanceCurrentDomain(FilterData):
    contract_address: str
    protocol_id: str
    wallet_address: str
    token_address: str
    block_transfer_value: int
    block_cumulative_value: int
    block_number: int
    block_timestamp: int
