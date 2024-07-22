from enum import IntFlag
from functools import reduce

from click import BadOptionUsage


class EntityType(IntFlag):
    BLOCK = 1 << 0
    TRANSACTION = 1 << 1
    LOG = 1 << 2
    TOKEN = 1 << 3
    TOKEN_TRANSFER = 1 << 4
    TRACE = 1 << 5
    CONTRACT = 1 << 6
    COIN_BALANCE = 1 << 7
    TOKEN_BALANCE = 1 << 8
    TOKEN_IDS = 1 << 9

    BRIDGE = 1 << 10

    @staticmethod
    def combine_all_entity_types():
        return reduce(lambda x, y: x | y, EntityType)

    @staticmethod
    def entity_filter_mode(entity_types):
        if entity_types ^ EntityType.BRIDGE == 0:
            return True
        return False

ALL_ENTITY_COLLECTIONS = EntityType.__members__.keys()
DEFAULT_COLLECTION = ["BLOCK", "TRANSACTION", "LOG", "TOKEN", "TOKEN_TRANSFER"]

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
