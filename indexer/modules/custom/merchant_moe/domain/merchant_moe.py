from dataclasses import dataclass

from indexer.domain import Domain, FilterData


@dataclass
class MerChantMoeTokenBin(FilterData):
    token_address: str
    token_id: int
    reserve0_bin: int
    reserve1_bin: int
    called_block_number: int
    called_block_timestamp: int
