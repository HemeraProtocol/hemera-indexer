from dataclasses import dataclass

from hemera.indexer.domains import Domain


@dataclass
class MerchantMoeErc1155TokenHolding(Domain):
    position_token_address: str
    wallet_address: str
    token_id: int
    balance: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoeErc1155TokenCurrentHolding(Domain):
    position_token_address: str
    wallet_address: str
    token_id: int
    balance: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoeErc1155TokenSupply(Domain):
    position_token_address: str
    token_id: int
    total_supply: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoeErc1155TokenCurrentSupply(Domain):
    position_token_address: str
    token_id: int
    total_supply: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoeTokenBin(Domain):
    position_token_address: str
    token_id: int
    reserve0_bin: int
    reserve1_bin: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoeTokenCurrentBin(Domain):
    position_token_address: str
    token_id: int
    reserve0_bin: int
    reserve1_bin: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoePool(Domain):
    position_token_address: str
    token0_address: str
    token1_address: str
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoePoolRecord(Domain):
    pool_address: str
    active_id: int
    bin_step: int
    block_number: int
    block_timestamp: int


@dataclass
class MerchantMoePoolCurrentStatus(Domain):
    pool_address: str
    active_id: int
    bin_step: int
    block_number: int
    block_timestamp: int
