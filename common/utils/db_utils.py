from typing import List, Type

from sqlalchemy import text

from common.models import HemeraModel, db
from common.services.postgresql_service import PostgreSQLService
from common.utils.config import get_config
from indexer.domain import Domain, dict_to_dataclass
from indexer.domain.block import Block
from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.jobs.source_job.pg_source_job import table_to_dataclass

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


def dataclass_builder(datas: List[Domain], domain: Type[Domain]):
    def build_block():
        blocks = [table_to_dataclass(data, Block) for data in datas]
        transactions = build_transaction()
        blocks_mapping = {block.hash: block for block in blocks}

        for block in blocks:
            block.transactions = []

        for transaction in transactions:
            blocks_mapping[transaction.block_hash].transactions.append(transaction)

        return blocks

    def build_transaction():
        transactions = [table_to_dataclass(data, Transaction) for data in datas]
        logs = build_log()
        transaction_mapping = {transaction.hash: transaction for transaction in transactions}

        for log in logs:
            transaction_mapping[log.transaction_hash].receipt.logs.append(log)

        return transactions

    def build_log():
        logs = [table_to_dataclass(data, Log) for data in datas]

        return logs

    special_build = {
        Block: build_block,
        Transaction: build_transaction,
        Log: build_log,
    }

    if domain in special_build:
        domains = special_build[domain]()
    else:
        domains = [table_to_dataclass(data, domain) for data in datas]

    return domains


def require_data_as_domain(
        service: PostgreSQLService, table: HemeraModel, columns: List[str], domain: Type[Domain]
) -> List[Domain]:
    """Read entire data from table and assemeble as a list of domain objects.

        This utility function fetches specified columns from a database table and converts
        each row into a domain object.

        Args:
            service: PostgreSQL service instance for database connection
            table: SQLAlchemy model class representing the database table
            columns: List of column names to retrieve from the table
            domain: Domain class to instantiate with the retrieved data

        Returns:
            List of domain objects populated with the database data

        Note:
            - Automatically handles session management
            - Converts SQL results to domain objects using dict_to_dataclass
            - Closes database session even if an error occurs

        Example:
            >>> blocks = require_data_as_domain(
            ...     service=pg_service,
            ...     table=Blocks,
            ...     domain=Block
            ... )
        """

    session = service.get_service_session()

    entities = build_entities(table, columns)

    try:
        datas = session.query(table).with_entities(*entities).all()
    finally:
        session.close()

    domains = dataclass_builder(datas, domain)
    return domains


def build_domains_by_sql(service: PostgreSQLService, domain: Type[Domain], sql: str) -> List[Domain]:
    """Read data by given sql and assemeble as a list of domain objects.

        This utility function executes a raw SQL query and assemeble each result row
        into a domain object.

        Args:
            service: PostgreSQL service instance for database connection
            domain: Domain class to instantiate with the query results
            sql: Raw SQL query string to execute

        Returns:
            List of domain objects populated with the query results

        Note:
            - Ensure SQL query returns columns that match domain class fields

        Example:
            >>> txs = build_domains_by_sql(
            ...     service=pg_service,
            ...     domain=Transaction,
            ...     sql="SELECT hash, from_address, to_address FROM transactions WHERE block_number > 1000 limit 100"
            ... )
        """
    session = service.get_service_session()

    try:
        datas = session.execute(text(sql))
    finally:
        session.close()

    domains = dataclass_builder(datas, domain)
    return domains
