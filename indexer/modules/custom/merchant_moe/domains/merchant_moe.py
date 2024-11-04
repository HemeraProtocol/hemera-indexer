from dataclasses import dataclass

from indexer.domain import Domain, FilterData


@dataclass
class MerchantMoeTokenBin(FilterData):
    position_token_address: str
    token_id: int
    reserve0_bin: int
    reserve1_bin: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoeTokenCurrentBin(FilterData):
    position_token_address: str
    token_id: int
    reserve0_bin: int
    reserve1_bin: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoePool(FilterData):
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
class MerchantMoePoolRecord(FilterData):
    pool_address: str
    active_id: int
    bin_step: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoePoolCurrentStatus(FilterData):
    pool_address: str
    active_id: int
    bin_step: int
    block_number: int
    block_timestamp: int
