from datetime import datetime, timedelta

from sqlalchemy import and_, func, or_

from hemera.api.app.cache import cache
from hemera.api.app.db_service.wallet_addresses import get_txn_cnt_by_address
from hemera.common.models import db
from hemera.common.models.scheduled_metadata import ScheduledMetadata
from hemera.common.models.transactions import Transactions
from hemera.common.utils.db_utils import build_entities
from hemera.common.utils.format_utils import hex_str_to_bytes
from hemera_udf.address_index.models.address_transactions import AddressTransactions
from hemera_udf.stats.models.daily_transactions_stats import DailyTransactionsStats

MAX_ADDRESS_TXN_COUNT = 100000


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


def get_address_transaction_cnt_v2(address: str):
    last_timestamp = db.session.query(func.max(ScheduledMetadata.last_data_timestamp)).scalar()
    bytes_address = hex_str_to_bytes(address)

    result = get_txn_cnt_by_address(address)
    past_txn_count = 0 if not result else result[0]

    if past_txn_count > MAX_ADDRESS_TXN_COUNT:
        return past_txn_count

    recently_txn_count = (
        db.session.query(AddressTransactions.address)
        .filter(
            and_(
                (AddressTransactions.block_timestamp >= last_timestamp if last_timestamp is not None else True),
                AddressTransactions.address == bytes_address,
            )
        )
        .count()
    )

    total_count = past_txn_count + recently_txn_count
    return total_count


def get_address_transaction_cnt(address: str):
    last_timestamp = db.session.query(func.max(ScheduledMetadata.last_data_timestamp)).scalar()
    bytes_address = hex_str_to_bytes(address)

    result = get_txn_cnt_by_address(address)
    past_txn_count = 0 if not result else result[0]
    if past_txn_count > MAX_ADDRESS_TXN_COUNT:
        return past_txn_count

    recently_txn_count = (
        db.session.query(Transactions.hash)
        .filter(
            and_(
                (Transactions.block_timestamp >= last_timestamp if last_timestamp is not None else True),
                or_(
                    Transactions.from_address == bytes_address,
                    Transactions.to_address == bytes_address,
                ),
            )
        )
        .count()
    )
    total_count = past_txn_count + recently_txn_count
    return total_count


def get_total_txn_count():
    # Get the latest block date and cumulative count
    latest_record = (
        DailyTransactionsStats.query.with_entities(
            DailyTransactionsStats.block_date,
            DailyTransactionsStats.total_cnt,
        )
        .order_by(DailyTransactionsStats.block_date.desc())
        .first()
    )

    # Check if the query returned a result
    if latest_record is None:
        return Transactions.query.count()

    block_date, cumulate_count = latest_record

    current_time = datetime.utcnow()

    ten_minutes_ago = current_time - timedelta(minutes=10)
    latest_10_min_txn_cnt = Transactions.query.filter(Transactions.block_timestamp >= ten_minutes_ago).count()

    avg_txn_per_minute = latest_10_min_txn_cnt / 10
    block_date_datetime = datetime.combine(block_date, datetime.min.time())

    minutes_since_last_block = int((current_time - block_date_datetime).total_seconds() / 60)

    estimated_txn = int(avg_txn_per_minute * minutes_since_last_block)

    return estimated_txn + cumulate_count


def get_transactions_by_condition(filter_condition=None, columns="*", limit=1, offset=0):
    entities = build_entities(Transactions, columns)

    transactions = (
        db.session.query(Transactions)
        .with_entities(*entities)
        .order_by(
            Transactions.block_number.desc(),
            Transactions.transaction_index.desc(),
        )
        .filter(filter_condition)
        .limit(limit)
        .offset(offset)
        .all()
    )

    return transactions


def get_transactions_cnt_by_condition(filter_condition=None, columns="*"):
    entities = build_entities(Transactions, columns)

    count = db.session.query(Transactions).with_entities(*entities).filter(filter_condition).count()

    return count
