from datetime import timedelta

from sqlalchemy import and_, func, or_

from api.app.cache import cache
from api.app.db_service.wallet_addresses import get_txn_cnt_by_address
from common.models import db
from common.models.daily_transactions_aggregates import DailyTransactionsAggregates
from common.models.scheduled_metadata import ScheduledWalletCountMetadata
from common.models.transactions import Transactions
from common.utils.db_utils import build_entities
from common.utils.format_utils import hex_str_to_bytes


def get_last_transaction():
    last_transaction = (
        db.session.query(Transactions)
        .with_entities(Transactions.block_timestamp)
        .order_by(Transactions.block_number.desc())
        .first()
    )
    return last_transaction


def get_transaction_by_hash(hash: str, columns="*"):
    bytes_hash = hex_str_to_bytes(hash)
    entities = build_entities(Transactions, columns)

    results = db.session.query(Transactions).with_entities(*entities).filter(Transactions.hash == bytes_hash).first()

    return results


def get_transactions_by_from_address(address, columns="*"):
    bytes_address = hex_str_to_bytes(address)
    entities = build_entities(Transactions, columns)

    results = (
        db.session.query(Transactions)
        .with_entities(*entities)
        .filter(Transactions.from_address == bytes_address)
        .first()
    )

    return results


def get_transactions_by_to_address(address, columns="*", limit=1):
    bytes_address = hex_str_to_bytes(address)
    entities = build_entities(Transactions, columns)

    results = (
        db.session.query(Transactions).with_entities(*entities).filter(Transactions.to_address == bytes_address).first()
    )

    return results


@cache.memoize(60)
def get_tps_latest_10min(timestamp):
    cnt = Transactions.query.filter(Transactions.block_timestamp >= (timestamp - timedelta(minutes=10))).count()
    return float(cnt / 600)


def get_address_transaction_cnt(address: str):
    last_timestamp = db.session.query(func.max(ScheduledWalletCountMetadata.last_data_timestamp)).scalar()
    bytes_address = hex_str_to_bytes(address)
    recently_txn_count = (
        db.session.query(Transactions.hash)
        .filter(
            and_(
                (Transactions.block_timestamp >= last_timestamp.date() if last_timestamp is not None else True),
                or_(
                    Transactions.from_address == bytes_address,
                    Transactions.to_address == bytes_address,
                ),
            )
        )
        .count()
    )

    result = get_txn_cnt_by_address(address)
    past_txn_count = 0 if not result else result[0]
    total_count = past_txn_count + recently_txn_count
    return total_count


def get_total_txn_count():
    # Get the latest block date and cumulative count
    latest_record = (
        DailyTransactionsAggregates.query.with_entities(
            DailyTransactionsAggregates.block_date,
            DailyTransactionsAggregates.total_cnt,
        )
        .order_by(DailyTransactionsAggregates.block_date.desc())
        .first()
    )

    # Check if the query returned a result
    if latest_record is None:
        return Transactions.query.count()

    block_date, cumulate_count = latest_record

    # Count transactions since the latest block date
    cnt = Transactions.query.filter(Transactions.block_timestamp >= (block_date + timedelta(days=1))).count()

    return cnt + cumulate_count


def get_transactions_by_condition(filter_condition=None, columns="*", limit=None, offset=None):
    entities = build_entities(Transactions, columns)

    statement = (
        db.session.query(Transactions)
        .with_entities(*entities)
        .order_by(
            Transactions.block_number.desc(),
            Transactions.transaction_index.desc(),
        )
        .filter(filter_condition)
    )
    if limit is not None:
        statement = statement.limit(limit)

    if offset is not None:
        statement = statement.offset(offset)

    transactions = statement.all()

    return transactions


def get_transactions_cnt_by_condition(filter_condition=None, columns="*"):
    entities = build_entities(Transactions, columns)

    count = db.session.query(Transactions).with_entities(*entities).filter(filter_condition).count()

    return count
