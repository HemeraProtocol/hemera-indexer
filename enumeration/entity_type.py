from enum import IntFlag

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


ALL_ENTITY_COLLECTIONS = EntityType.__members__.keys()
BASIC_COLLECTION = ["BLOCK", "TRANSACTION", "LOG"]


def calculate_entity_value(entity_types):
    entities = 0
    for entity_type in [entity.strip().upper() for entity in entity_types.split(',')]:
        if entity_type not in ALL_ENTITY_COLLECTIONS:
            raise BadOptionUsage(
                '--entity-type', '{} is not an available entity type. Supply a comma separated list of types from {}'
                .format(entity_type, ','.join(ALL_ENTITY_COLLECTIONS)))
        else:
            if entity_type == EntityType.BLOCK.name:
                entities = entities | EntityType.BLOCK
            elif entity_type == EntityType.TRANSACTION.name:
                entities = entities | EntityType.TRANSACTION
            elif entity_type == EntityType.LOG.name:
                entities = entities | EntityType.LOG
            elif entity_type == EntityType.TOKEN.name:
                entities = entities | EntityType.TOKEN
            elif entity_type == EntityType.TOKEN_TRANSFER.name:
                entities = entities | EntityType.TOKEN_TRANSFER
            elif entity_type == EntityType.TRACE.name:
                entities = entities | EntityType.TRACE
            elif entity_type == EntityType.CONTRACT.name:
                entities = entities | EntityType.CONTRACT
            elif entity_type == EntityType.COIN_BALANCE.name:
                entities = entities | EntityType.COIN_BALANCE
            else:
                pass
    return entities
