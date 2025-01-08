from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Type

from sqlalchemy import text

from hemera.common.models import HemeraModel, db
from hemera.common.models.blocks import Blocks
from hemera.common.services.postgresql_service import PostgreSQLService
from hemera.common.utils.config import get_config
from hemera.common.utils.format_utils import bytes_to_hex_str
from hemera.indexer.domains import Domain, dict_to_dataclass
from hemera.indexer.domains.block import Block
from hemera.indexer.domains.log import Log
from hemera.indexer.domains.receipt import Receipt
from hemera.indexer.domains.transaction import Transaction

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


def table_to_dataclass(row_instance, cls):
    """
    Converts row of table to a dataclass instance, handling nested structures.

    Args:
        row_instance (HemeraModel): The input data structure.
        cls: The dataclass type to convert to.

    Returns:
        An instance of the dataclass which is corresponding to table in the definition.
    """

    dict_instance = {}
    if hasattr(row_instance, "__table__"):
        for column in row_instance.__table__.columns:
            if column.name == "meta_data":
                meta_data_json = getattr(row_instance, column.name)
                if meta_data_json:
                    for key in meta_data_json:
                        dict_instance[key] = meta_data_json[key]
            else:
                value = getattr(row_instance, column.name)
                dict_instance[column.name] = convert_value(value)
    else:
        for column, value in row_instance._asdict().items():
            dict_instance[column] = convert_value(value)

    domain = dict_to_dataclass(dict_instance, cls)
    if cls is Transaction:
        domain.fill_with_receipt(Receipt.from_pg(dict_instance))

    return domain


def convert_value(value):
    if isinstance(value, datetime):
        return int(round(value.replace(tzinfo=timezone.utc).timestamp()))
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, bytes):
        return bytes_to_hex_str(value)
    elif isinstance(value, memoryview):
        return bytes_to_hex_str(bytes(value))
    elif isinstance(value, list):
        return [convert_value(v) for v in value]
    elif isinstance(value, dict):
        return {k: convert_value(v) for k, v in value.items()}
    else:
        return value


def dataclass_builder(datas: list, domain: Type[Domain]):
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
    service: PostgreSQLService,
    table: HemeraModel,
    domain: Type[Domain],
    columns: List[str] = "*",
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
