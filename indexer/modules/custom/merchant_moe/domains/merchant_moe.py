from dataclasses import dataclass

from indexer.domain import Domain, FilterData


@dataclass
class MerChantMoeTokenBin(FilterData):
    position_token_address: str
    token_id: int
    reserve0_bin: int
    reserve1_bin: int
    block_number: int
    block_timestamp: int


@dataclass
class MerChantMoeTokenCurrentBin(FilterData):
    position_token_address: str
    token_id: int
    reserve0_bin: int
    reserve1_bin: int
    block_number: int
    block_timestamp: int


@dataclass
class MerChantMoePool(FilterData):
    position_token_address: str
    token0_address: str
    token1_address: str
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoeErc1155TokenSupply(FilterData):
    position_token_address: str
    token_id: int
    total_supply: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoeErc1155TokenCurrentSupply(FilterData):
    position_token_address: str
    token_id: int
    total_supply: int
    block_number: int
    block_timestamp: int


@dataclass
class MerChantMoePoolRecord(FilterData):
    pool_address: str
    active_id: int
    bin_step: int
    block_number: int
    block_timestamp: int


@dataclass
class MerChantMoePoolCurrentStatus(FilterData):
    pool_address: str
    active_id: int
    bin_step: int
    block_number: int
    block_timestamp: int
