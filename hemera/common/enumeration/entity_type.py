from enum import IntFlag
from functools import reduce
from typing import Dict, Generator, Set, Type

from hemera.indexer.domains.block import Block, UpdateBlockInternalCount
from hemera.indexer.domains.block_ts_mapper import BlockTsMapper
from hemera.indexer.domains.contract import Contract
from hemera.indexer.domains.contract_internal_transaction import ContractInternalTransaction
from hemera.indexer.domains.current_token_balance import CurrentTokenBalance
from hemera.indexer.domains.log import Log
from hemera.indexer.domains.token import Token, UpdateToken
from hemera.indexer.domains.token_balance import TokenBalance
from hemera.indexer.domains.token_id_infos import (
    ERC721TokenIdChange,
    ERC721TokenIdDetail,
    ERC1155TokenIdDetail,
    UpdateERC721TokenIdDetail,
    UpdateERC1155TokenIdDetail,
)
from hemera.indexer.domains.token_transfer import ERC20TokenTransfer, ERC721TokenTransfer, ERC1155TokenTransfer
from hemera.indexer.domains.trace import Trace
from hemera.indexer.domains.transaction import Transaction


class DynamicEntityTypeRegistry:
    """Registry for managing entity type registrations, output mappings and dynamic types."""

    _next_bit = 14  # Start after the last predefined bit in EntityType
    _dynamic_types: Dict[str, int] = {}
    _output_types: Dict[int, Set[Type]] = {}

    @classmethod
    def register(cls, name: str) -> int:
        """Register a new entity type and return its bit value."""
        if name in cls._dynamic_types:
            return cls._dynamic_types[name]

        if hasattr(EntityType, name):
            return getattr(EntityType, name)

        bit_value = 1 << cls._next_bit
        cls._dynamic_types[name] = bit_value
        cls._next_bit += 1
        return bit_value

    @classmethod
    def register_output_types(cls, entity_type: int, output_types: Set[Type]) -> None:
        """Register output types for a specific entity type flag."""
        cls._output_types[entity_type] = output_types

    @classmethod
    def get_value(cls, name: str) -> int:
        """Get the bit value for a registered type."""
        return cls._dynamic_types.get(name)

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a type is registered."""
        return name in cls._dynamic_types

    @classmethod
    def get_all_types(cls):
        """Get all registered types including both static and dynamic."""
        static_types = {name: value for name, value in EntityType.__members__.items()}
        return {**static_types, **cls._dynamic_types}

    @classmethod
    def get_output_types(cls, entity_types: int) -> Generator[Type, None, None]:
        """Get all output types for given entity types, removing duplicates."""
        seen_types = set()
        # Check static output types first
        for bit_value, types in StaticOutputTypes._output_types.items():
            if entity_types & bit_value:
                for type_class in types:
                    if type_class not in seen_types:
                        seen_types.add(type_class)
                        yield type_class

        # Then check dynamic output types
        for bit_value, types in cls._output_types.items():
            if entity_types & bit_value:
                for type_class in types:
                    if type_class not in seen_types:
                        seen_types.add(type_class)
                        yield type_class


class StaticOutputTypes:
    """Manages output types for static EntityType members."""

    _output_types: Dict[int, Set[Type]] = {}

    @classmethod
    def register_output_types(cls, entity_type: int, output_types: Set[Type]) -> None:
        """Register output types for a static entity type."""
        cls._output_types[entity_type] = output_types


class EntityType(IntFlag):
    """
    Entity types using bit flags with both static and dynamic types.
    Static types are defined here, dynamic types are managed by DynamicEntityTypeRegistry.
    """

    # Core package
    EXPLORER_BASE = 1 << 0
    EXPLORER_TOKEN = 1 << 1
    EXPLORER_TRACE = 1 << 2

    # Composite type
    EXPLORER = EXPLORER_BASE | EXPLORER_TOKEN | EXPLORER_TRACE

    @staticmethod
    def combine_all_entity_types():
        """Combine all entity types using bitwise OR."""
        all_values = list(EntityType.__members__.values())
        all_values.extend(DynamicEntityTypeRegistry._dynamic_types.values())
        return reduce(lambda x, y: x | y, all_values)

    @staticmethod
    def entity_filter_mode(entity_types):
        """Check if entity types match bridge mode exactly."""
        if entity_types ^ EntityType.BRIDGE == 0:
            return True
        return False


DEFAULT_COLLECTION = []


def register_all_output_types():
    """Register output types for all entity types (both static and dynamic)."""
    # Register static output types
    StaticOutputTypes.register_output_types(EntityType.EXPLORER_BASE, {Block, BlockTsMapper, Transaction, Log})

    StaticOutputTypes.register_output_types(
        EntityType.EXPLORER_TOKEN,
        {
            Token,
            UpdateToken,
            ERC20TokenTransfer,
            ERC721TokenTransfer,
            ERC1155TokenTransfer,
            TokenBalance,
            CurrentTokenBalance,
            UpdateERC1155TokenIdDetail,
            ERC1155TokenIdDetail,
            UpdateERC721TokenIdDetail,
            ERC721TokenIdDetail,
            ERC721TokenIdChange,
        },
    )

    StaticOutputTypes.register_output_types(
        EntityType.EXPLORER_TRACE,
        {
            Trace,
            Contract,
            ContractInternalTransaction,
            UpdateBlockInternalCount,
            # CoinBalance
        },
    )


register_all_output_types()


def calculate_entity_value(entity_types: str) -> int:
    """Convert entity type strings to combined bit value."""
    if entity_types is None or entity_types == "":
        return 0

    entities = EntityType(0)
    for entity_type in [entity.strip().upper() for entity in entity_types.split(",")]:
        if entity_type in EntityType.__members__:
            entities |= EntityType[entity_type]
        elif DynamicEntityTypeRegistry.is_registered(entity_type):
            entities |= DynamicEntityTypeRegistry.get_value(entity_type)
        else:
            all_types = list(EntityType.__members__.keys())
            all_types.extend(DynamicEntityTypeRegistry._dynamic_types.keys())
            available_types = ",".join(all_types)
            raise ValueError(
                f"{entity_type} is not an available entity type. Supply a comma-separated list of types from {available_types}"
            )
    return entities


def generate_output_types(entity_types: int) -> Generator[Type, None, None]:
    """Generate output types for both static and dynamic entity types."""
    yield from DynamicEntityTypeRegistry.get_output_types(entity_types)
