from dataclasses import dataclass

from indexer.domains import FilterData


@dataclass
class AddressTokenDeposit(FilterData):
    wallet_address: str
    chain_id: int
    contract_address: str
    token_address: str
    value: int
    block_number: int
    block_timestamp: int
