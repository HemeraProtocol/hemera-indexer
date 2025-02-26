#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/3 04:01
# @Author  ideal93
# @File  test_logs.py
# @Brief
from datetime import datetime, timedelta
from typing import List

import pytest
from sqlmodel import Session

from hemera.app.api.routes.developer.es_adapter.helper import APILogResponse, get_event_logs
from hemera.common.models.logs import Logs
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture
def sample_logs(session: Session):
    base_time = datetime(2025, 1, 1, 12, 0, 0)

    topicA = hex_str_to_bytes("0x" + "A" * 64)
    topicB = hex_str_to_bytes("0x" + "B" * 64)
    topicC = hex_str_to_bytes("0x" + "C" * 64)
    topicD = hex_str_to_bytes("0x" + "D" * 64)
    topicE = hex_str_to_bytes("0x" + "E" * 64)
    empty_topic = hex_str_to_bytes("0x" + "0" * 64)

    logs = [
        # Log 1
        Logs(
            transaction_hash=hex_str_to_bytes("0x" + "a" * 64),
            log_index=0,
            address=hex_str_to_bytes("0x1111111111111111111111111111111111111111"),
            data=hex_str_to_bytes("0x11"),
            block_number=1000,
            block_timestamp=base_time,
            block_hash=hex_str_to_bytes("0x" + "a" * 64),
            topic0=topicA,
            topic1=topicB,
            topic2=topicC,
            topic3=topicD,
        ),
        # Log 2
        Logs(
            transaction_hash=hex_str_to_bytes("0x" + "b" * 64),
            log_index=1,
            address=hex_str_to_bytes("0x2222222222222222222222222222222222222222"),
            data=hex_str_to_bytes("0x11"),
            block_number=1001,
            block_hash=hex_str_to_bytes("0x" + "b" * 64),
            block_timestamp=base_time + timedelta(minutes=1),
            topic0=topicA,
            topic1=topicE,  # Using topicE instead of topicB here
            topic2=topicC,
            topic3=empty_topic,  # Not None, but an "empty" value
        ),
        # Log 3
        Logs(
            transaction_hash=hex_str_to_bytes("0x" + "c" * 64),
            log_index=2,
            address=hex_str_to_bytes("0x3333333333333333333333333333333333333333"),
            data=hex_str_to_bytes("0x11"),
            block_number=1002,
            block_hash=hex_str_to_bytes("0x" + "c" * 64),
            block_timestamp=base_time + timedelta(minutes=2),
            topic0=hex_str_to_bytes("0x" + "F" * 64),
            topic1=topicB,
            topic2=empty_topic,
            topic3=topicD,
        ),
        # Log 4
        Logs(
            transaction_hash=hex_str_to_bytes("0x" + "d" * 64),
            log_index=3,
            address=hex_str_to_bytes("0x1111111111111111111111111111111111111111"),
            data=hex_str_to_bytes("0x11"),
            block_number=1003,
            block_hash=hex_str_to_bytes("0x" + "d" * 64),
            block_timestamp=base_time + timedelta(minutes=3),
            topic0=topicA,
            topic1=topicB,
            topic2=topicC,
            topic3=topicE,
        ),
        # Log 5
        Logs(
            transaction_hash=hex_str_to_bytes("0x" + "e" * 64),
            log_index=4,
            address=hex_str_to_bytes("0x4444444444444444444444444444444444444444"),
            data=hex_str_to_bytes("0x11"),
            block_number=1004,
            block_hash=hex_str_to_bytes("0x" + "e" * 64),
            block_timestamp=base_time + timedelta(minutes=4),
            topic0=empty_topic,
            topic1=topicB,
            topic2=topicC,
            topic3=topicD,
        ),
        # Log 6 (for pagination)
        Logs(
            transaction_hash=hex_str_to_bytes("0x" + "f" * 64),
            log_index=5,
            address=hex_str_to_bytes("0x5555555555555555555555555555555555555555"),
            data=hex_str_to_bytes("0x11"),
            block_number=1005,
            block_hash=hex_str_to_bytes("0x" + "f" * 64),
            block_timestamp=base_time + timedelta(minutes=5),
            topic0=topicA,
            topic1=topicB,
            topic2=topicC,
            topic3=topicD,
        ),
    ]

    session.add_all(logs)
    session.commit()
    return logs


def test_get_event_logs_no_filters(session: Session, sample_logs):
    """
    Test that get_event_logs returns all logs when no topic or address filters are applied.
    """
    result: List[APILogResponse] = get_event_logs(
        session=session, from_block=1000, to_block=1010, page=1, offset=10, sort_order="asc"
    )
    # Expect all 6 logs to be returned
    assert len(result) == 6

    # Verify the order by block_number ascending.
    block_numbers = [int(r.blockNumber) for r in result]
    assert block_numbers == sorted(block_numbers)


def test_get_event_logs_filter_by_topic0(session: Session, sample_logs):
    """
    Test filtering by topic0.
    """
    # Use topicA (as hex string) for filtering.
    topicA_str = "0x" + "A" * 64
    result: List[APILogResponse] = get_event_logs(
        session=session, topic0=topicA_str, from_block=1000, to_block=1010, page=1, offset=10, sort_order="asc"
    )
    # In our sample, logs 1, 2, 4, and 6 have topic0 equal to topicA.
    assert len(result) == 4
    for log in result:
        returned_topic0 = log.topics[0]
        assert returned_topic0.lower() == topicA_str.lower()


def test_get_event_logs_filter_by_address(session: Session, sample_logs):
    """
    Test filtering logs by address.
    """
    target_address = "0x1111111111111111111111111111111111111111".lower()
    result: List[APILogResponse] = get_event_logs(
        session=session, address=target_address, from_block=1000, to_block=1010, page=1, offset=10, sort_order="asc"
    )
    # Two logs have this address (logs 1 and 4)
    assert len(result) == 2
    for log in result:
        assert log.address.lower() == target_address


def test_get_event_logs_combined_topics_and(session: Session, sample_logs):
    """
    Test filtering logs with combined topics using the AND operator.
    """
    # We want logs that have topic0 = topicA and topic1 = topicB.
    topicA_str = "0x" + "A" * 64
    topicB_str = "0x" + "B" * 64
    result: List[APILogResponse] = get_event_logs(
        session=session,
        topic0=topicA_str,
        topic1=topicB_str,
        topic0_1_opr="and",
        from_block=1000,
        to_block=1010,
        page=1,
        offset=10,
        sort_order="asc",
    )
    # Expected logs: 1, 4, and 6 have topic0 equal to topicA and topic1 equal to topicB.
    assert len(result) == 3
    for log in result:
        assert topicA_str.lower() in log.topics
        assert topicB_str.lower() in log.topics


def test_get_event_logs_combined_topics_or(session: Session, sample_logs):
    """
    Test filtering logs with combined topics using the OR operator.
    """
    # Request logs that have topic0 = topicA OR topic1 = topicE.
    topicA_str = "0x" + "A" * 64
    topicE_str = "0x" + "E" * 64
    result: List[APILogResponse] = get_event_logs(
        session=session,
        topic0=topicA_str,
        topic1=topicE_str,
        topic0_1_opr="or",
        from_block=1000,
        to_block=1010,
        page=1,
        offset=10,
        sort_order="asc",
    )
    # Expected:
    #   - Logs with topic0 == topicA: logs 1, 2, 4, 6.
    #   - Logs with topic1 == topicE: log 2 (already counted) and possibly others.
    # Overall, we expect 4 logs.
    assert len(result) == 4
    for log in result:
        assert (topicA_str.lower() in log.topics) or (topicE_str.lower() in log.topics)


def test_get_event_logs_pagination_and_sort(session: Session, sample_logs):
    """
    Test pagination and sorting.
    """
    # Request logs with offset=2 in descending order.
    result_page1: List[APILogResponse] = get_event_logs(
        session=session, from_block=1000, to_block=1010, page=1, offset=2, sort_order="desc"
    )
    result_page2: List[APILogResponse] = get_event_logs(
        session=session, from_block=1000, to_block=1010, page=2, offset=2, sort_order="desc"
    )
    # Verify pagination: page1 should have 2 logs, page2 should have the next 2.
    assert len(result_page1) == 2
    assert len(result_page2) == 2

    # Verify sort order: descending order means page1 has the highest block numbers.
    blocks_page1 = [int(r.blockNumber) for r in result_page1]
    blocks_page2 = [int(r.blockNumber) for r in result_page2]
    assert blocks_page1[0] >= blocks_page1[1]
    # The last block in page1 should be greater than the first block in page2.
    assert blocks_page1[-1] > blocks_page2[0]


def test_get_event_logs_block_range(session: Session, sample_logs):
    """
    Test filtering logs by block range.
    """
    # Set block range to only include logs from block 1002 to 1004.
    result: List[APILogResponse] = get_event_logs(
        session=session, from_block=1002, to_block=1004, page=1, offset=10, sort_order="asc"
    )
    block_numbers = sorted([int(r.blockNumber) for r in result])
    assert block_numbers == [1002, 1003, 1004]


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
