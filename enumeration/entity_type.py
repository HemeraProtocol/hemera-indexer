from enum import IntFlag
from functools import reduce

from indexer.domain.block import Block, UpdateBlockInternalCount
from indexer.domain.block_ts_mapper import BlockTsMapper
from indexer.domain.coin_balance import CoinBalance
from indexer.domain.contract import Contract
from indexer.domain.contract_internal_transaction import ContractInternalTransaction
from indexer.domain.current_token_balance import CurrentTokenBalance
from indexer.domain.log import Log
from indexer.domain.token import *
from indexer.domain.token_balance import TokenBalance
from indexer.domain.token_id_infos import *
from indexer.domain.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from indexer.domain.trace import Trace
from indexer.domain.transaction import Transaction
from indexer.modules.custom.address_index.domain import *
from indexer.modules.custom.blue_chip.domain.feature_blue_chip import BlueChipHolder
from indexer.modules.custom.erc20_token_holding.domain.erc20_token_holding import (
    Erc20CurrentTokenHolding,
    Erc20TokenHolding,
)
from indexer.modules.custom.merchant_moe.domain.erc1155_token_holding import (
    MerchantMoeErc1155TokenCurrentHolding,
    MerchantMoeErc1155TokenCurrentSupply,
    MerchantMoeErc1155TokenHolding,
    MerchantMoeErc1155TokenSupply,
)
from indexer.modules.custom.merchant_moe.domain.merchant_moe import MerChantMoeTokenBin, MerChantMoeTokenCurrentBin
from indexer.modules.custom.staking_fbtc.domain.feature_staked_fbtc_detail import StakedFBTCDetail, TransferedFBTCDetail
from indexer.modules.custom.total_supply.domain.erc20_total_supply import Erc20CurrentTotalSupply, Erc20TotalSupply
from indexer.modules.custom.uniswap_v2.domain.feature_uniswap_v2 import (
    UniswapV2CurrentLiquidityHolding,
    UniswapV2LiquidityHolding,
    UniswapV2Pool,
    UniswapV2PoolCurrentReserves,
    UniswapV2PoolCurrentTotalSupply,
    UniswapV2PoolReserves,
    UniswapV2PoolTotalSupply,
)
from indexer.modules.custom.uniswap_v3.domain.feature_uniswap_v3 import (
    UniswapV3Pool,
    UniswapV3PoolCurrentPrice,
    UniswapV3PoolPrice,
    UniswapV3Token,
    UniswapV3TokenCurrentStatus,
    UniswapV3TokenDetail,
)
from indexer.modules.user_ops.domain.user_operations import UserOperationsResult


class EntityType(IntFlag):
    EXPLORER_BASE = 1 << 0
    EXPLORER_TOKEN = 1 << 1
    EXPLORER_TRACE = 1 << 2

    BRIDGE = 1 << 3
    UNISWAP_V3 = 1 << 4

    USER_OPS = 1 << 5

    BLUE_CHIP = 1 << 6

    EXPLORER = EXPLORER_BASE | EXPLORER_TOKEN | EXPLORER_TRACE

    MANTLE_20 = 1 << 7
    UNISWAP_V2 = 1 << 8
    STAKED_FBTC = 1 << 9
    MERCHANT = 1 << 10
    ADDRESS_INDEX = 1 << 11
    FBTC_ETH = 1 << 12

    @staticmethod
    def combine_all_entity_types():
        return reduce(lambda x, y: x | y, EntityType)

    @staticmethod
    def entity_filter_mode(entity_types):
        if entity_types ^ EntityType.BRIDGE == 0:
            return True
        return False


ALL_ENTITY_COLLECTIONS = EntityType.__members__.keys()
DEFAULT_COLLECTION = ["EXPLORER_BASE", "EXPLORER_TOKEN"]


def calculate_entity_value(entity_types):
    entities = EntityType(0)
    for entity_type in [entity.strip().upper() for entity in entity_types.split(",")]:
        if entity_type in EntityType.__members__:
            entities |= EntityType[entity_type]
        else:
            available_types = ",".join(ALL_ENTITY_COLLECTIONS)
            raise ValueError(
                f"{entity_type} is not an available entity type. Supply a comma-separated list of types from {available_types}"
            )
    return entities


def generate_output_types(entity_types):
    if entity_types & EntityType.EXPLORER_BASE:
        yield Block
        yield BlockTsMapper
        yield Transaction
        yield Log

    if entity_types & EntityType.EXPLORER_TOKEN:
        yield Token
        yield UpdateToken
        yield ERC20TokenTransfer
        yield ERC721TokenTransfer
        yield ERC1155TokenTransfer
        yield TokenBalance
        yield CurrentTokenBalance

        yield UpdateERC1155TokenIdDetail
        yield ERC1155TokenIdDetail
        yield UpdateERC721TokenIdDetail
        yield ERC721TokenIdDetail
        yield ERC721TokenIdChange

    if entity_types & EntityType.EXPLORER_TRACE:
        yield Trace
        yield Contract
        yield CoinBalance
        yield ContractInternalTransaction
        yield UpdateBlockInternalCount

    if entity_types & EntityType.UNISWAP_V3:
        yield ERC721TokenTransfer
        yield Token
        yield UniswapV3Pool
        yield UniswapV3Token
        yield UniswapV3PoolPrice
        yield UniswapV3TokenDetail
        yield UniswapV3PoolCurrentPrice
        yield UniswapV3TokenCurrentStatus
        yield UpdateToken
        yield TokenBalance
        yield CurrentTokenBalance
        yield Log

    if entity_types & EntityType.USER_OPS:
        yield UserOperationsResult

    if entity_types & EntityType.ADDRESS_INDEX:
        yield Block
        yield Transaction
        yield Log
        yield Token
        yield ERC20TokenTransfer
        yield ERC721TokenTransfer
        yield AddressNftTransfer
        yield AddressTokenHolder
        yield AddressTokenTransfer
        yield TokenAddressNftInventory
        yield AddressTransaction

    if entity_types & EntityType.BLUE_CHIP:
        yield Block
        yield Transaction
        yield ERC721TokenTransfer
        yield Token
        yield UpdateToken
        yield TokenBalance
        yield CurrentTokenBalance
        yield BlueChipHolder

    if entity_types & EntityType.MANTLE_20:
        yield Block
        yield Transaction
        yield ERC20TokenTransfer
        yield Token
        yield UpdateToken
        yield TokenBalance
        yield CurrentTokenBalance
        yield Erc20TotalSupply
        yield Erc20TokenHolding
    if entity_types & EntityType.UNISWAP_V2:
        yield UniswapV2Pool
        yield UniswapV2PoolTotalSupply
        yield UniswapV2PoolCurrentTotalSupply
        yield UniswapV2PoolReserves
        yield UniswapV2PoolCurrentReserves
        yield UniswapV2LiquidityHolding
        yield UniswapV2CurrentLiquidityHolding
        yield Token
    if entity_types & EntityType.STAKED_FBTC:
        yield Block
        yield Transaction
        yield Log
        yield ERC20TokenTransfer
        yield Token
        yield UpdateToken
        yield StakedFBTCDetail

    if entity_types & EntityType.MERCHANT:
        yield Block
        yield Transaction
        yield Log
        yield ERC1155TokenTransfer
        yield Token
        yield UpdateToken
        yield MerchantMoeErc1155TokenHolding
        yield MerchantMoeErc1155TokenCurrentHolding
        yield MerchantMoeErc1155TokenSupply
        yield MerchantMoeErc1155TokenCurrentSupply
        yield MerChantMoeTokenBin
        yield MerChantMoeTokenCurrentBin

    if entity_types & EntityType.FBTC_ETH:
        # yield ERC721TokenTransfer
        # yield ERC721TokenIdChange
        # yield UpdateERC721TokenIdDetail
        # yield ERC721TokenIdDetail
        yield Token
        yield UpdateToken
        yield TokenBalance
        yield CurrentTokenBalance
        # yield UniswapV3Pool
        # yield UniswapV3Token
        # yield UniswapV3PoolPrice
        # yield UniswapV3TokenDetail
        # yield UniswapV3PoolCurrentPrice
        # yield UniswapV3TokenCurrentStatus
        yield Log
        yield Erc20TokenHolding
        yield ERC20TokenTransfer
        yield Erc20CurrentTokenHolding
        yield Erc20TotalSupply
        yield Erc20CurrentTotalSupply
        yield TransferedFBTCDetail
        yield StakedFBTCDetail
