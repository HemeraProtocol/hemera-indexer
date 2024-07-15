from common.models import db
from common.models.blocks import Blocks


def get_last_block():
    lastest_block = (
        db.session.query(Blocks)
        .with_entities(Blocks.number, Blocks.timestamp)
        .order_by(Blocks.number.desc())
        .first()
    )

    return lastest_block


def get_block_by_number(block_number: int):
    block = (
        db.session.query(Blocks)
        .with_entities(Blocks.number, Blocks.timestamp)
        .filter(Blocks.number == block_number)
        .first()
    )

    return block
