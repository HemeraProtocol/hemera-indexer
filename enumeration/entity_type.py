from enum import IntFlag
from functools import reduce

from indexer.domain.block import Block, UpdateBlockInternalCount
from indexer.domain.coin_balance import CoinBalance
from indexer.domain.contract import Contract
from indexer.domain.contract_internal_transaction import ContractInternalTransaction
from indexer.modules.custom.uniswap_v3.domain.feature_uniswap_v3 import UniswapV3Pool
from indexer.domain.log import Log
from indexer.domain.token import *
from indexer.domain.token_balance import TokenBalance
from indexer.domain.current_token_balance import CurrentTokenBalance
from indexer.domain.token_id_infos import *
from indexer.domain.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from indexer.domain.trace import Trace
from indexer.domain.transaction import Transaction


class EntityType(IntFlag):
    EXPLORER_BASE = 1 << 0
    EXPLORER_TOKEN = 1 << 1
    EXPLORER_TRACE = 1 << 2

    BRIDGE = 1 << 3
    UNISWAP_V3_POOL = 1 << 4

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
DEFAULT_COLLECTION = ["EXPLORER_BASE", "EXPLORER_TOKEN"]


def calculate_entity_value(entity_types):
    entities = EntityType(0)
    for entity_type in [entity.strip().upper() for entity in entity_types.split(',')]:
        if entity_type in EntityType.__members__:
            entities |= EntityType[entity_type]
        else:
            available_types = ','.join(ALL_ENTITY_COLLECTIONS)
            raise ValueError(
                f'{entity_type} is not an available entity type. Supply a comma-separated list of types from {available_types}')
    return entities


def generate_output_types(entity_types):
    if entity_types & EntityType.EXPLORER_BASE:
        yield Block
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

    if entity_types & EntityType.UNISWAP_V3_POOL:
        yield UniswapV3Pool
