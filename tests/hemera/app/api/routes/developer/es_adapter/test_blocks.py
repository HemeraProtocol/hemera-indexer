#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/4 12:37
# @Author  ideal93
# @File  test_blocks.py
# @Brief
from datetime import datetime, timedelta

import pytest
from sqlmodel import Session, delete

from hemera.app.api.routes.developer.es_adapter.helper import block_number_by_timestamp
from hemera.common.models.blocks import Blocks
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture(autouse=True)
def clean_blocks(session: Session):
    session.exec(delete(Blocks))
    session.commit()


@pytest.fixture
def sample_blocks(session: Session):
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    blocks = [
        Blocks(number=100, timestamp=base_time, hash=hex_str_to_bytes(f"0x{'%064x' % 100}")),
        Blocks(number=101, timestamp=base_time + timedelta(minutes=1), hash=hex_str_to_bytes(f"0x{'%064x' % 101}")),
        Blocks(number=102, timestamp=base_time + timedelta(minutes=2), hash=hex_str_to_bytes(f"0x{'%064x' % 102}")),
        Blocks(number=103, timestamp=base_time + timedelta(minutes=3), hash=hex_str_to_bytes(f"0x{'%064x' % 103}")),
        Blocks(number=104, timestamp=base_time + timedelta(minutes=4), hash=hex_str_to_bytes(f"0x{'%064x' % 104}")),
    ]
    session.add_all(blocks)
    session.commit()
    return blocks


def test_block_number_before(session: Session, sample_blocks):
    """
    Test the "before" option:
    Given a timestamp, the function should return the block with the greatest timestamp
    that is less than or equal to the given timestamp.
    """
    # Use a timestamp that falls between block 101 and 102.
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    # Timestamp for 1 minute and 30 seconds after base_time.
    test_timestamp = int((base_time + timedelta(minutes=1, seconds=30)).timestamp())
    test_timestamp = test_timestamp
    # Expect block number 101 because:
    #   Block 100: base_time (0 minutes)
    #   Block 101: base_time + 1 minute
    #   Block 102: base_time + 2 minutes (too high)
    result = block_number_by_timestamp(session, test_timestamp, "before")
    assert result == 101, f"Expected block number 101 but got {result}"


def test_block_number_after(session: Session, sample_blocks):
    """
    Test the "after" option:
    Given a timestamp, the function should return the block with the smallest timestamp
    that is greater than or equal to the given timestamp.
    """
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    # Timestamp for 1 minute and 30 seconds after base_time.
    test_timestamp = (base_time + timedelta(minutes=1, seconds=30)).timestamp()

    # Expect block number 102 because:
    #   Block 102 has timestamp base_time + 2 minutes, which is the smallest timestamp >= test_timestamp.
    result = block_number_by_timestamp(session, test_timestamp, "after")
    assert result == 102, f"Expected block number 102 but got {result}"


def test_block_number_by_timestamp_exact_match(session: Session, sample_blocks):
    """
    Test the function when the timestamp exactly matches one of the block timestamps.
    """
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    exact_timestamp = base_time.timestamp()  # exactly block 100's timestamp

    # For "before" and "after", an exact match should return that block number.
    result_before = block_number_by_timestamp(session, exact_timestamp, "before")
    result_after = block_number_by_timestamp(session, exact_timestamp, "after")
    assert result_before == 100, f"Expected block number 100 but got {result_before}"
    assert result_after == 100, f"Expected block number 100 but got {result_after}"


def test_block_number_invalid_closest(session: Session, sample_blocks):
    """
    Test that an invalid value for closest returns None.
    """
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    test_timestamp = base_time.timestamp()

    result = block_number_by_timestamp(session, test_timestamp, "invalid")
    assert result is None, "Expected None for an invalid closest parameter"


def test_block_number_no_block_before(session: Session, sample_blocks):
    """
    Test the scenario where no block exists before the given timestamp.
    For example, if the timestamp is earlier than the earliest block timestamp.
    """
    # Set a timestamp earlier than the first block's timestamp.
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    test_timestamp = (base_time - timedelta(seconds=1)).timestamp()

    result = block_number_by_timestamp(session, test_timestamp, "before")
    # No block exists before this timestamp so result should be None.
    assert result is None, f"Expected None but got {result}"


def test_block_number_no_block_after(session: Session, sample_blocks):
    """
    Test the scenario where no block exists after the given timestamp.
    For example, if the timestamp is later than the latest block timestamp.
    """
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    # Set a timestamp later than the last block's timestamp.
    test_timestamp = (base_time + timedelta(minutes=5, seconds=1)).timestamp()

    result = block_number_by_timestamp(session, test_timestamp, "after")
    # No block exists after this timestamp so result should be None.
    assert result is None, f"Expected None but got {result}"


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
