from enum import IntFlag
from functools import reduce

from custom_jobs.address_index.domains import *
from custom_jobs.address_index.domains.address_contract_operation import AddressContractOperation
from custom_jobs.address_index.domains.address_internal_transaction import AddressInternalTransaction
from custom_jobs.address_index.domains.address_nft_1155_holders import AddressNft1155Holder
from custom_jobs.blue_chip.domains.feature_blue_chip import BlueChipHolder
from custom_jobs.deposit_to_l2.domains.address_token_deposit import AddressTokenDeposit
from custom_jobs.deposit_to_l2.domains.token_deposit_transaction import TokenDepositTransaction
from custom_jobs.eigen_layer.domains.eigen_layer_domain import EigenLayerAction, EigenLayerAddressCurrent
from custom_jobs.hemera_ens.domains.ens_domain import (
    ENSAddressChangeD,
    ENSAddressD,
    ENSMiddleD,
    ENSNameRenewD,
    ENSRegisterD,
)
from custom_jobs.karak.domains.karak_domain import KarakActionD, KarakAddressCurrentD, KarakVaultTokenD
from custom_jobs.opensea.domains.address_opensea_transactions import AddressOpenseaTransaction
from custom_jobs.opensea.domains.opensea_order import OpenseaOrder
from custom_jobs.uniswap_v3.domains.feature_uniswap_v3 import (
    UniswapV3Pool,
    UniswapV3PoolCurrentPrice,
    UniswapV3PoolPrice,
    UniswapV3SwapEvent,
    UniswapV3Token,
    UniswapV3TokenCollectFee,
    UniswapV3TokenCurrentStatus,
    UniswapV3TokenDetail,
    UniswapV3TokenUpdateLiquidity,
)
from indexer.domains.all_features_value_record import AllFeatureValueRecordBlueChipHolders
from indexer.domains.block import Block, UpdateBlockInternalCount
from indexer.domains.block_ts_mapper import BlockTsMapper
from indexer.domains.contract import Contract
from indexer.domains.contract_internal_transaction import ContractInternalTransaction
from indexer.domains.current_token_balance import CurrentTokenBalance
from indexer.domains.log import Log
from indexer.domains.token import *
from indexer.domains.token_balance import TokenBalance
from indexer.domains.token_id_infos import *
from indexer.domains.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from indexer.domains.trace import Trace
from indexer.domains.transaction import Transaction
from indexer.modules.user_ops.domain.user_operations import UserOperationsResult


class EntityType(IntFlag):
    EXPLORER_BASE = 1 << 0
    EXPLORER_TOKEN = 1 << 1
    EXPLORER_TRACE = 1 << 2

    BRIDGE = 1 << 3

    UNISWAP_V3 = 1 << 4

    USER_OPS = 1 << 5

    BLUE_CHIP = 1 << 6

    ADDRESS_INDEX = 1 << 7

    DEPOSIT_TO_L2 = 1 << 8

    OPEN_SEA = 1 << 9

    ENS = 1 << 10

    KARAK = 1 << 11

    EIGEN_LAYER = 1 << 13

    EXPLORER = EXPLORER_BASE | EXPLORER_TOKEN | EXPLORER_TRACE

    @staticmethod
    def combine_all_entity_types():
        return reduce(lambda x, y: x | y, EntityType)

    @staticmethod
    def entity_filter_mode(entity_types):
        if entity_types ^ EntityType.BRIDGE == 0:
            return True
        return False


ALL_ENTITY_COLLECTIONS = EntityType.__members__.keys()
DEFAULT_COLLECTION = []


def calculate_entity_value(entity_types):
    if entity_types is None or entity_types == "":
        return 0
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
        # yield CoinBalance
        yield ContractInternalTransaction
        yield UpdateBlockInternalCount

    if entity_types & EntityType.UNISWAP_V3:
        yield Token
        yield UpdateToken
        yield UniswapV3Pool
        yield UniswapV3SwapEvent
        yield UniswapV3PoolPrice
        yield UniswapV3PoolCurrentPrice
        yield UniswapV3Token
        yield UniswapV3TokenCollectFee
        yield UniswapV3TokenUpdateLiquidity
        yield UniswapV3TokenDetail
        yield UniswapV3TokenCurrentStatus

    if entity_types & EntityType.USER_OPS:
        yield UserOperationsResult

    if entity_types & EntityType.ADDRESS_INDEX:
        yield Block
        yield Transaction
        yield Log
        yield Token
        yield ERC20TokenTransfer
        yield ERC721TokenTransfer
        yield ERC1155TokenTransfer
        yield AddressNftTransfer
        yield AddressTokenHolder
        yield AddressTokenTransfer
        yield TokenAddressNftInventory
        yield AddressTransaction
        yield AddressNft1155Holder
        yield AddressContractOperation
        yield AddressInternalTransaction

    if entity_types & EntityType.BLUE_CHIP:
        yield Block
        yield Transaction
        yield ERC721TokenTransfer
        yield Token
        yield UpdateToken
        yield TokenBalance
        yield CurrentTokenBalance
        yield AllFeatureValueRecordBlueChipHolders
        yield BlueChipHolder

    if entity_types & EntityType.DEPOSIT_TO_L2:
        yield TokenDepositTransaction
        yield AddressTokenDeposit

    if entity_types & EntityType.ENS:
        yield ENSMiddleD
        yield ENSRegisterD
        yield ENSNameRenewD
        yield ENSAddressChangeD
        yield ENSAddressD

    if entity_types & EntityType.OPEN_SEA:
        yield AddressOpenseaTransaction
        yield OpenseaOrder

    if entity_types & EntityType.KARAK:
        yield KarakActionD
        yield KarakVaultTokenD
        yield KarakAddressCurrentD

    if entity_types & EntityType.EIGEN_LAYER:
        yield EigenLayerAction
        yield EigenLayerAddressCurrent
