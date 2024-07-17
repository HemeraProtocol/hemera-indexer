from enum import IntFlag
from functools import reduce

from click import BadOptionUsage


class EntityType(IntFlag):
    BLOCK = 1
    TRANSACTION = 2
    LOG = 4
    TOKEN = 8
    TOKEN_TRANSFER = 16
    TRACE = 32
    CONTRACT = 64
    COIN_BALANCE = 128
    TOKEN_BALANCE = 256
    TOKEN_IDS = 512

    @staticmethod
    def combine_all_entity_types():
        return reduce(lambda x, y: x | y, EntityType)


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
