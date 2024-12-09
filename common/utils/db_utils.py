from typing import List

from sqlalchemy import text

from common.models import HemeraModel, db
from common.services.postgresql_service import PostgreSQLService
from common.utils.config import get_config
from indexer.domain import Domain, dict_to_dataclass

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


def require_data_as_domain(
    service: PostgreSQLService, table: HemeraModel, columns: List[str], domain: Domain
) -> List[Domain]:
    session = service.get_service_session()

    entities = build_entities(table, columns)

    try:
        datas = session.query(table).with_entities(*entities).all()
    finally:
        session.close()

    domains = [dict_to_dataclass(data, domain) for data in datas]
    return domains


def build_domains_by_sql(service: PostgreSQLService, domain: Domain, sql: str) -> List[Domain]:
    session = service.get_service_session()

    try:
        datas = session.execute(text(sql))
    finally:
        session.close()

    domains = [dict_to_dataclass(data, domain) for data in datas]
    return domains
