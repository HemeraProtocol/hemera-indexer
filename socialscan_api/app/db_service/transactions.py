from datetime import timedelta

from sqlalchemy import or_

from common.models import db
from common.models.daily_transactions_aggreggates import DailyTransactionsAggregates
from common.models.transactions import Transactions
from socialscan_api.app.cache import cache
from socialscan_api.app.db_service.wallet_addresses import get_txn_cnt_by_address


def get_last_transaction():
    last_transaction = (db.session.query(Transactions)
                        .with_entities(Transactions.block_timestamp)
                        .order_by(Transactions.block_number.desc())
                        .first())
    return last_transaction


@cache.memoize(60)
def get_tps_latest_10min(timestamp):
    cnt = Transactions.query.filter(Transactions.block_timestamp >= (timestamp - timedelta(minutes=10))).count()
    return float(cnt / 600)


def get_address_transaction_cnt(address):
    # last_timestamp = db.session.query(func.max(ScheduledWalletCountMetadata.last_data_timestamp)).scalar()
    recently_txn_count = (
        db.session.query(Transactions.hash)
        .filter(
            or_(
                Transactions.from_address == bytes(address, 'utf-8'),
                Transactions.to_address == bytes(address, 'utf-8'),
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
