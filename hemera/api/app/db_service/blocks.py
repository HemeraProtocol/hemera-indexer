from hemera.common.models import db
from hemera.common.models.blocks import Blocks
from hemera.common.utils.db_utils import build_entities
from hemera.common.utils.format_utils import hex_str_to_bytes


def get_last_block(columns="*"):
    entities = build_entities(Blocks, columns)

    latest_block = db.session.query(Blocks).with_entities(*entities).order_by(Blocks.number.desc()).first()

    return latest_block


def get_block_by_number(block_number: int, columns="*"):
    entities = build_entities(Blocks, columns)

    block = db.session.query(Blocks).with_entities(*entities).filter(Blocks.number == block_number).first()

    return block


def get_block_by_hash(hash: str, columns="*"):
    bytes_hash = hex_str_to_bytes(hash)
    entities = build_entities(Blocks, columns)

    results = db.session.query(Blocks).with_entities(*entities).filter(Blocks.hash == bytes_hash).first()

    return results


def get_blocks_by_condition(filter_condition=None, columns="*", limit=None, offset=None):
    entities = build_entities(Blocks, columns)

    statement = db.session.query(Blocks).with_entities(*entities)

    if filter_condition is not None:
        statement = statement.filter(filter_condition)

    statement = statement.order_by(Blocks.number.desc())

    if limit is not None:
        statement = statement.limit(limit)

    if offset is not None:
        statement = statement.offset(offset)

    return statement.all()
