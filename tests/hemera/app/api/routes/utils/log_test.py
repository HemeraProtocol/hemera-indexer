from datetime import datetime, timedelta

import pytest

from hemera.app.api.routes.helper.log import _get_logs_by_address, _get_logs_by_hash
from hemera.common.models.logs import Logs
from hemera.common.utils.format_utils import hex_str_to_bytes


@pytest.fixture
def sample_logs(session):
    current_time = datetime.utcnow()
    logs = [
        # Two logs for same transaction
        Logs(
            log_index=1,
            transaction_hash=hex_str_to_bytes("0x644aee68ccb38d2a74901f3e1279419fd62481b5567a56bcb479c38d4fd5b379"),
            block_hash=hex_str_to_bytes("0x6511c8974f8341a2a4f30fcff201cee1863364e978e85f9f667912d4874a3bbc"),
            address=hex_str_to_bytes("0x1111111111111111111111111111111111111111"),
            data=hex_str_to_bytes("0xf7d8c88300000000000000000000000000000000000000000000000000000000"),
            topic0=hex_str_to_bytes("0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65"),
            topic1=hex_str_to_bytes("0x000000000000000000000000b4c79dab8f259c7aee6e5b2aa729821864227e84"),
            block_number=100,
            block_timestamp=current_time,
            transaction_index=0,
        ),
        Logs(
            log_index=2,
            transaction_hash=hex_str_to_bytes("0x644aee68ccb38d2a74901f3e1279419fd62481b5567a56bcb479c38d4fd5b379"),
            block_hash=hex_str_to_bytes("0x6511c8974f8341a2a4f30fcff201cee1863364e978e85f9f667912d4874a3bbc"),
            address=hex_str_to_bytes("0x1111111111111111111111111111111111111111"),
            data=hex_str_to_bytes("0xf7d8c88300000000000000000000000000000000000000000000000000000001"),
            topic0=hex_str_to_bytes("0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b66"),
            block_number=100,
            block_timestamp=current_time,
            transaction_index=0,
        ),
        # One log for second transaction
        Logs(
            log_index=1,
            transaction_hash=hex_str_to_bytes("0x74c72e9e6f3aa88e896cc7d9d526bdf0934d3f9c8fe178d0ed46f21d9c466434"),
            block_hash=hex_str_to_bytes("0xa945dc8e514fd116ecf87e6692dceb3692131694ab412ace1cfa01fd899581c5"),
            address=hex_str_to_bytes("0x2222222222222222222222222222222222222222"),
            data=hex_str_to_bytes("0xf7d8c88300000000000000000000000000000000000000000000000000000002"),
            topic0=hex_str_to_bytes("0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b67"),
            block_number=101,
            block_timestamp=current_time - timedelta(seconds=12),
            transaction_index=0,
        ),
    ]

    for log in logs:
        session.add(log)
    session.commit()

    return logs


def test_get_logs_by_hash(session, sample_logs):
    # Test full select
    hash_str = "0x644aee68ccb38d2a74901f3e1279419fd62481b5567a56bcb479c38d4fd5b379"
    logs = _get_logs_by_hash(session, hash_str)
    assert len(logs) == 2
    for log in logs:
        assert log.transaction_hash == hex_str_to_bytes(hash_str)
        assert log.topic0 is not None  # Required field
        assert log.address is not None  # Required field
        assert isinstance(log.block_hash, bytes)
        assert isinstance(log.topic0, bytes)

    # Test specific columns
    logs = _get_logs_by_hash(session, hash_str, columns=["log_index", "topic0", "address"])
    assert len(logs) == 2
    log_indices = {log.log_index for log in logs}
    assert log_indices == {1, 2}
    for log in logs:
        assert hasattr(log, "log_index")
        assert hasattr(log, "topic0")
        assert hasattr(log, "address")
        assert isinstance(log.topic0, bytes)
        assert isinstance(log.address, bytes)
        with pytest.raises(AttributeError):
            _ = log.data  # Should not have data field

    # Test non-existent hash
    logs = _get_logs_by_hash(session, "0xffffffffffffffff")
    assert len(logs) == 0

    # Test invalid hash format
    with pytest.raises(ValueError):
        _get_logs_by_hash(session, "invalid_hash")


def test_get_logs_by_address(session, sample_logs):
    address = "0x1111111111111111111111111111111111111111"

    # Test full select
    logs = _get_logs_by_address(session, address)
    assert len(logs) == 2
    for log in logs:
        assert log.address == hex_str_to_bytes(address)
        assert isinstance(log.topic0, bytes)
        assert isinstance(log.block_hash, bytes)

    # Test pagination
    logs = _get_logs_by_address(session, address, limit=1)
    assert len(logs) == 1

    logs = _get_logs_by_address(session, address, offset=1, limit=1)
    assert len(logs) == 1
    assert logs[0].log_index == 1

    # Test specific columns
    logs = _get_logs_by_address(session, address, columns=["log_index", "topic0", "address"])
    assert len(logs) == 2
    for log in logs:
        assert hasattr(log, "log_index")
        assert hasattr(log, "topic0")
        assert hasattr(log, "address")
        assert isinstance(log.topic0, bytes)
        assert isinstance(log.address, bytes)
        assert log.address == hex_str_to_bytes(address)
        with pytest.raises(AttributeError):
            _ = log.data  # Should not have data field

    # Test non-existent address
    logs = _get_logs_by_address(session, "0x9999999999999999999999999999999999999999")
    assert len(logs) == 0

    # Test invalid address format
    with pytest.raises(ValueError):
        _get_logs_by_address(session, "invalid_address")


def test_logs_transaction_isolation(session, sample_logs):
    address = "0x1111111111111111111111111111111111111111"

    with session.begin():
        new_log = Logs(
            log_index=3,
            transaction_hash=hex_str_to_bytes("0x644aee68ccb38d2a74901f3e1279419fd62481b5567a56bcb479c38d4fd5b379"),
            block_hash=hex_str_to_bytes("0x6511c8974f8341a2a4f30fcff201cee1863364e978e85f9f667912d4874a3bbc"),
            address=hex_str_to_bytes(address),
            data=hex_str_to_bytes("0xf7d8c88300000000000000000000000000000000000000000000000000000003"),
            topic0=hex_str_to_bytes("0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b68"),
            block_number=100,
            block_timestamp=sample_logs[0].block_timestamp,
            transaction_index=0,
        )
        session.add(new_log)

        # Should see the new log inside transaction
        logs = _get_logs_by_address(session, address)
        assert len(logs) == 3

        session.rollback()

    # Should not see the new log after rollback
    logs = _get_logs_by_address(session, address)
    assert len(logs) == 2


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
