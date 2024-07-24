from enum import IntFlag
from functools import reduce

from click import BadOptionUsage


class EntityType(IntFlag):
    EXPLORER_BASE = 1 << 0
    EXPLORER_TOKEN = 1 << 1
    EXPLORER_TRACE = 1 << 2

    BRIDGE = 1 << 3

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
