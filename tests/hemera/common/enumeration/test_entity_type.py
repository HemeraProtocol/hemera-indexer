import pytest

from hemera.common.enumeration.entity_type import (
    DynamicEntityTypeRegistry,
    EntityType,
    StaticOutputTypes,
    calculate_entity_value,
    generate_output_types,
)
from hemera.indexer.domains.block import Block
from hemera.indexer.domains.log import Log
from hemera.indexer.domains.token import Token
from hemera.indexer.domains.trace import Trace


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_entity_type_basic():
    """Test basic EntityType definitions"""
    assert EntityType.EXPLORER_BASE == 1 << 0
    assert EntityType.EXPLORER_TOKEN == 1 << 1
    assert EntityType.EXPLORER_TRACE == 1 << 2
    assert EntityType.EXPLORER == EntityType.EXPLORER_BASE | EntityType.EXPLORER_TOKEN | EntityType.EXPLORER_TRACE


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_dynamic_entity_type_registration():
    """Test registering new dynamic entity types"""
    # Reset registry state
    DynamicEntityTypeRegistry._next_bit = 14
    DynamicEntityTypeRegistry._dynamic_types = {}

    test_type = DynamicEntityTypeRegistry.register("TEST_TYPE")
    assert test_type == 1 << 14

    # Test duplicate registration returns same value
    duplicate_type = DynamicEntityTypeRegistry.register("TEST_TYPE")
    assert duplicate_type == test_type


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_output_type_registration():
    """Test registration of output types for both static and dynamic types"""
    # Reset registries
    StaticOutputTypes._output_types = {}
    DynamicEntityTypeRegistry._output_types = {}

    # Register static output types
    base_types = {Block, Log}
    StaticOutputTypes.register_output_types(EntityType.EXPLORER_BASE, base_types)

    # Register dynamic output types
    test_type = DynamicEntityTypeRegistry.register("TEST_TYPE")
    test_types = {Token, Trace}
    DynamicEntityTypeRegistry.register_output_types(test_type, test_types)

    # Test retrieval through generate_output_types
    combined_types = EntityType.EXPLORER_BASE | test_type
    retrieved_types = set(generate_output_types(combined_types))
    assert retrieved_types == base_types | test_types


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_calculate_entity_value_valid():
    """Test calculate_entity_value with valid inputs"""
    # Test single type
    value = calculate_entity_value("EXPLORER_BASE")
    assert value == EntityType.EXPLORER_BASE

    # Test multiple types
    value = calculate_entity_value("EXPLORER_BASE,EXPLORER_TOKEN")
    assert value == EntityType.EXPLORER_BASE | EntityType.EXPLORER_TOKEN

    # Test with dynamic type
    test_type = DynamicEntityTypeRegistry.register("TEST_TYPE")
    value = calculate_entity_value("EXPLORER_BASE,TEST_TYPE")
    assert value == EntityType.EXPLORER_BASE | test_type


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_calculate_entity_value_invalid():
    """Test calculate_entity_value with invalid inputs"""
    # Test empty input
    assert calculate_entity_value("") == 0
    assert calculate_entity_value(None) == 0

    # Test invalid type
    with pytest.raises(ValueError) as excinfo:
        calculate_entity_value("INVALID_TYPE")
    assert "is not an available entity type" in str(excinfo.value)


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_combine_all_entity_types():
    """Test combining all entity types including dynamic ones"""
    # Register a dynamic type
    test_type = DynamicEntityTypeRegistry.register("TEST_TYPE")

    # Get combined value
    all_types = EntityType.combine_all_entity_types()

    # Verify includes both static and dynamic
    assert all_types & EntityType.EXPLORER != 0
    assert all_types & test_type != 0
    assert all_types & (EntityType.EXPLORER_BASE | EntityType.EXPLORER_TOKEN | EntityType.EXPLORER_TRACE) != 0


@pytest.mark.indexer
@pytest.mark.indexer_utils
def test_duplicate_output_type_handling():
    """Test handling of duplicate output types across different entity types"""
    # Reset registries
    StaticOutputTypes._output_types = {}
    DynamicEntityTypeRegistry._output_types = {}

    # Register same type for different entities
    common_type = {Block}
    StaticOutputTypes.register_output_types(EntityType.EXPLORER_BASE, common_type)
    StaticOutputTypes.register_output_types(EntityType.EXPLORER_TOKEN, common_type)

    # Verify duplicates are removed
    combined_types = EntityType.EXPLORER_BASE | EntityType.EXPLORER_TOKEN
    retrieved_types = list(generate_output_types(combined_types))
    assert len(retrieved_types) == 1
    assert Block in retrieved_types
