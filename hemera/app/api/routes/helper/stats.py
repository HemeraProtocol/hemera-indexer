from typing import Any, List, Tuple, Union

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlmodel import select

from hemera.common.models.stats.daily_transactions_stats import DailyTransactionsStats


def get_daily_transactions_cnt(
    session: Session, columns: Union[str, List[Union[str, Tuple[str, str]]]] = "*", limit: int = 10
) -> List[Any]:
    """
    Get daily transactions count, ordered by block date descending.

    Args:
        session: Database session
        columns: Column names to select. Can be:
                - "*" for all columns
                - A single column name
                - A list of column names
                - A list of tuples (column_name, label)
        limit: Maximum number of records to return

    Returns:
        List of DailyTransactionsStats objects or tuples depending on columns parameter
    """
    if columns == "*":
        stmt = select(DailyTransactionsStats)
    else:
        if isinstance(columns, str):
            columns = [columns]

        # Handle both simple column names and (column, label) tuples
        select_columns = []
        for col in columns:
            if isinstance(col, tuple):
                col_name, label = col
                select_columns.append(getattr(DailyTransactionsStats, col_name).label(label))
            else:
                select_columns.append(getattr(DailyTransactionsStats, col))

        stmt = select(*select_columns)

    stmt = stmt.order_by(DailyTransactionsStats.block_date.desc()).limit(limit)

    return session.execute(stmt).all()
