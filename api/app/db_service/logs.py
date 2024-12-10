from common.models import db
from common.models.logs import Logs
from common.models.transactions import Transactions
from common.utils.format_utils import hex_str_to_bytes


def get_logs_with_input_by_hash(hash, columns="*"):
    bytes_hash = hex_str_to_bytes(hash.lower())
    # Always get FUll Logs now

    logs = (
        db.session.query(Logs)
        .filter(Logs.transaction_hash == bytes_hash, Logs.block_timestamp == Transactions.block_timestamp)
        .join(Transactions, Logs.transaction_hash == Transactions.hash)
        .add_columns(Transactions.input)
        .all()
    )

    return logs


def get_logs_with_input_by_address(address: str, limit=None, offset=None):
    address_bytes = hex_str_to_bytes(address.lower())

    statement = (
        db.session.query(Logs)
        .filter(Logs.address == address_bytes)
        .join(Transactions, Logs.transaction_hash == Transactions.hash)
        .add_columns(Transactions.input)
    )

    if limit is not None:
        statement = statement.limit(limit)

    if offset is not None:
        statement = statement.offset(offset)

    logs = statement.all()

    return logs
