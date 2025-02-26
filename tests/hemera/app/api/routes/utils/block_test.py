from datetime import datetime, timedelta

import pytest

from hemera.app.api.routes.helper.block import *
from hemera.app.api.routes.helper.block import (
    _get_block_by_hash,
    _get_block_by_number,
    _get_blocks_by_condition,
    _get_last_block,
)
from hemera.common.models.blocks import Blocks
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture
def sample_blocks(session):
    blocks = [
        Blocks(
            number=21436149,
            hash=hex_str_to_bytes("0x644aee68ccb38d2a74901f3e1279419fd62481b5567a56bcb479c38d4fd5b379"),
            parent_hash=hex_str_to_bytes("0x74c72e9e6f3aa88e896cc7d9d526bdf0934d3f9c8fe178d0ed46f21d9c466434"),
            timestamp=datetime.utcnow(),
        ),
        Blocks(
            number=21436148,
            hash=hex_str_to_bytes("0x74c72e9e6f3aa88e896cc7d9d526bdf0934d3f9c8fe178d0ed46f21d9c466434"),
            parent_hash=hex_str_to_bytes("0x5ad9a7c932709efac7d0e0d28c762bfde1737167f6eb51572f6797acece4c957"),
            timestamp=datetime.utcnow() - timedelta(seconds=12),
        ),
        Blocks(
            number=21436147,
            hash=hex_str_to_bytes("0x5ad9a7c932709efac7d0e0d28c762bfde1737167f6eb51572f6797acece4c957"),
            parent_hash=hex_str_to_bytes("0x5ad9a7c932709efac7d0e0d28c762bfde1737167f6eb51572f6797acece4c957"),
            timestamp=datetime.utcnow() - timedelta(seconds=24),
        ),
    ]

    for block in blocks:
        session.add(block)
    session.commit()

    return blocks


def test_get_last_block(session, sample_blocks):
    block = _get_last_block(session)
    assert block is not None
    assert block.number == 21436149
    assert block.hash == hex_str_to_bytes("0x644aee68ccb38d2a74901f3e1279419fd62481b5567a56bcb479c38d4fd5b379")

    block = _get_last_block(session, columns=["number", "hash"])
    assert block.number == 21436149
    assert block.hash == hex_str_to_bytes("0x644aee68ccb38d2a74901f3e1279419fd62481b5567a56bcb479c38d4fd5b379")
    with pytest.raises(AttributeError):
        _ = block.timestamp


def test_get_block_by_number(session, sample_blocks):
    block = _get_block_by_number(session, 21436148)
    assert block is not None
    assert block.number == 21436148
    assert block.hash == hex_str_to_bytes("0x74c72e9e6f3aa88e896cc7d9d526bdf0934d3f9c8fe178d0ed46f21d9c466434")

    block = _get_block_by_number(session, 999)
    assert block is None

    block_number = _get_block_by_number(session, 21436148, columns=["number"])
    assert block_number == 21436148


def test_get_block_by_hash(session, sample_blocks):
    block = _get_block_by_hash(session, "0x74c72e9e6f3aa88e896cc7d9d526bdf0934d3f9c8fe178d0ed46f21d9c466434")
    assert block is not None
    assert block.number == 21436148
    assert block.hash == hex_str_to_bytes("0x74c72e9e6f3aa88e896cc7d9d526bdf0934d3f9c8fe178d0ed46f21d9c466434")

    block = _get_block_by_hash(session, "0xffff")
    assert block is None

    with pytest.raises(ValueError):
        _get_block_by_hash(session, "invalid_hash")


def test_get_blocks_by_condition(session, sample_blocks):
    blocks = _get_blocks_by_condition(session)
    assert len(blocks) == 3
    assert blocks[0].number == 21436149

    blocks = _get_blocks_by_condition(session, filter_condition=(Blocks.number > 21436147))
    assert len(blocks) == 2
    assert all(b.number > 21436147 for b in blocks)

    blocks = _get_blocks_by_condition(session, filter_condition=Blocks.number.between(21436147, 21436149))
    assert len(blocks) == 3

    # Test hash in condition
    target_hashes = [
        hex_str_to_bytes("0x644aee68ccb38d2a74901f3e1279419fd62481b5567a56bcb479c38d4fd5b379"),
        hex_str_to_bytes("0x74c72e9e6f3aa88e896cc7d9d526bdf0934d3f9c8fe178d0ed46f21d9c466434"),
    ]
    blocks = _get_blocks_by_condition(session, filter_condition=Blocks.hash.in_(target_hashes))
    assert len(blocks) == 2
    assert all(block.hash in target_hashes for block in blocks)

    # Test timestamp between condition
    first_block_time = sample_blocks[0].timestamp
    last_block_time = sample_blocks[-1].timestamp
    blocks = _get_blocks_by_condition(
        session, filter_condition=Blocks.timestamp.between(last_block_time, first_block_time)
    )
    assert len(blocks) == 3
    assert all(last_block_time <= block.timestamp <= first_block_time for block in blocks)

    blocks = _get_blocks_by_condition(session, limit=2)
    assert len(blocks) == 2
    assert blocks[0].number == 21436149

    blocks = _get_blocks_by_condition(session, offset=1, limit=1)
    assert len(blocks) == 1
    assert blocks[0].number == 21436148

    blocks = _get_blocks_by_condition(session, columns="number")
    assert len(blocks) == 3
    with pytest.raises(AttributeError):
        _ = blocks[0].hash


def test_transaction_isolation(session, sample_blocks):
    with session.begin():
        new_block = Blocks(
            number=21436150,
            hash=hex_str_to_bytes("0xdef0"),
            parent_hash=hex_str_to_bytes("0x644aee68ccb38d2a74901f3e1279419fd62481b5567a56bcb479c38d4fd5b379"),
            timestamp=datetime.utcnow(),
        )
        session.add(new_block)

        last_block = _get_last_block(session)
        assert last_block.number == 21436150

        session.rollback()

    last_block = _get_last_block(session)
    assert last_block.number == 21436149


def test_get_blocks_default_order(session, sample_blocks):
    blocks = _get_blocks_by_condition(session)
    assert len(blocks) == 3
    assert [b.number for b in blocks] == [21436149, 21436148, 21436147]


def test_get_blocks_number_asc(session, sample_blocks):
    blocks = _get_blocks_by_condition(session, order_by=Blocks.number.asc())
    assert len(blocks) == 3
    assert [b.number for b in blocks] == [21436147, 21436148, 21436149]


def test_get_blocks_timestamp_desc(session, sample_blocks):
    blocks = _get_blocks_by_condition(session, order_by=Blocks.timestamp.desc())
    assert len(blocks) == 3
    assert blocks[0].number == 21436149
    assert blocks[1].number == 21436148
    assert blocks[2].number == 21436147


def test_get_blocks_multiple_order(session, sample_blocks):
    blocks = _get_blocks_by_condition(session, order_by=[Blocks.timestamp.asc(), Blocks.number.desc()])
    assert len(blocks) == 3
    assert blocks[0].number == 21436147
    assert blocks[1].number == 21436148
    assert blocks[2].number == 21436149


def test_get_blocks_columns_with_order(session, sample_blocks):
    blocks = _get_blocks_by_condition(session, columns=["number", "timestamp"], order_by=Blocks.timestamp.asc())
    assert len(blocks) == 3
    assert hasattr(blocks[0], "number")
    assert hasattr(blocks[0], "timestamp")
    with pytest.raises(AttributeError):
        _ = blocks[0].hash
    assert blocks[0].number == 21436147
    assert blocks[1].number == 21436148
    assert blocks[2].number == 21436149


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
