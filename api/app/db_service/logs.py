from common.models import db
from common.models.logs import Logs
from common.models.transactions import Transactions
from common.utils.db_utils import build_entities


def get_logs_with_input_by_hash(hash, columns='*'):
    bytes_hash = bytes.fromhex(hash.lower()[2:])
    # Always get FUll Logs now

    logs = (
        db.session.query(Logs)
        .filter(Logs.transaction_hash == bytes_hash)
        .join(Transactions, Logs.transaction_hash == Transactions.hash)
        .add_columns(Transactions.input)
        .all()
    )

    return logs


def get_logs_with_input_by_address(address: str, limit=None, offset=None):
    address_bytes = bytes.fromhex(address.lower()[2:])

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
