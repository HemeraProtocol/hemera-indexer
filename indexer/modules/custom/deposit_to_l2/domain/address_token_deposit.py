from dataclasses import dataclass

from indexer.domain import FilterData


@dataclass
class AddressTokenDeposit(FilterData):
    wallet_address: str
    chain: str
    token_address: str
    value: int
    block_number: int
