from sqlalchemy import text

from common.models import db
from common.utils.config import get_config

app_config = get_config()


def build_entities(model, columns):
    if columns == "*":
        entities = [attr for attr in model.__table__.columns]
    else:
        entities = []
        for column in columns:
            if isinstance(column, tuple):
                col, alias = column
                entities.append(getattr(model, col).label(alias))
            else:
                entities.append(getattr(model, column))

    return entities


def get_total_row_count(table):
    estimate_transaction = db.session.execute(
        text(
            f"""
            SELECT reltuples::bigint AS estimate FROM pg_class where oid = '{app_config.db_read_sql_alchemy_database_config.schema}.{table}'::regclass;
        """
        )
    ).fetchone()
    return estimate_transaction[0]
