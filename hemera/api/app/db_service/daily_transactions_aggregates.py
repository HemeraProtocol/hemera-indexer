from hemera.common.models import db
from hemera.common.utils.db_utils import build_entities
from hemera_udf.stats.models.daily_transactions_stats import DailyTransactionsStats


def get_daily_transactions_cnt(columns="*", limit=10):
    entities = build_entities(DailyTransactionsStats, columns)

    results = (
        db.session.query(DailyTransactionsStats)
        .with_entities(*entities)
        .order_by(DailyTransactionsStats.block_date.desc())
        .limit(limit)
    )

    return results
