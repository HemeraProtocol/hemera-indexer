from common.models import db
from common.models.daily_transactions_aggregates import DailyTransactionsAggregates
from common.utils.db_utils import build_entities


def get_daily_transactions_cnt(columns="*", limit=10):
    entities = build_entities(DailyTransactionsAggregates, columns)

    results = (
        db.session.query(DailyTransactionsAggregates)
        .with_entities(*entities)
        .order_by(DailyTransactionsAggregates.block_date.desc())
        .limit(limit)
    )

    return results
