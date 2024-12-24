import logging
from typing import List

import click
from sqlalchemy import text

from hemera.cli.options.storage import postgres, postgres_initial
from hemera.common.logo import print_logo
from hemera.common.models import HemeraModel
from hemera.common.services.postgresql_service import PostgreSQLService
from hemera.common.utils.module_loading import import_submodules

logger = logging.getLogger("DB Client")


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@postgres
@postgres_initial
@click.option(
    "-c",
    "--create-tables",
    type=str,
    default=None,
    required=False,
    help="Table names that need to be created in the database. e.g. blocks,transactions",
)
@click.option(
    "-d",
    "--drop-tables",
    type=str,
    default=None,
    required=False,
    help="Table names that need to be dropped in the database. e.g. blocks,transactions",
)
@click.option(
    "-t",
    "--truncate-tables",
    type=str,
    default=None,
    required=False,
    help="Table names that need to clean up data. e.g. blocks,transactions",
)
def db(postgres_url, init_schema, db_version, create_tables=None, drop_tables=None, truncate_tables=None):
    print_logo()
    service = PostgreSQLService(jdbc_url=postgres_url, db_version=db_version, init_schema=init_schema)

    if create_tables or drop_tables or truncate_tables:
        import_submodules("hemera_udf")
        exist_models = {
            table.__tablename__: table
            for table in HemeraModel.get_all_hemera_model_dict()
            if hasattr(table, "__tablename__")
        }

        if create_tables:
            tables = create_tables.split(",")
            if len(tables) > 0:
                create(service, tables, exist_models)

            logger.info("Table creation has been finished.")

        if drop_tables:
            tables = drop_tables.split(",")
            if len(tables) > 0:
                drop(service, tables, exist_models)

            logger.info("Table deletion has been finished.")

        if truncate_tables:
            tables = truncate_tables.split(",")
            if len(tables) > 0:
                truncate(service, tables, exist_models)

            logger.info("Table cleanup has been finished.")

    logger.info("db operation finished, now exit.")


def create(service: PostgreSQLService, tables: List[str], exist_models: dict):
    engine = service.get_service_engine()
    for table in tables:
        if table in exist_models:
            exist_models[table].__table__.create(engine, checkfirst=True)
            logger.info(f"Table {table} created successfully.")
        else:
            logger.warning(f"No Table {table} model definition was found.")


def drop(service: PostgreSQLService, tables: List[str], exist_models: dict):
    engine = service.get_service_engine()
    for table in tables:
        if table in exist_models:
            exist_models[table].__table__.drop(engine, checkfirst=True)
            logger.info(f"Table {table} dropped successfully.")
        else:
            logger.warning(f"No Table {table} model definition was found.")


def truncate(service: PostgreSQLService, tables: List[str], exist_models: dict):
    session = service.get_service_session()
    for table in tables:
        if table in exist_models:
            session.execute(text(f"TRUNCATE TABLE {table}"))
            session.commit()
            logger.info(f"Table {table} truncated successfully.")
        else:
            logger.warning(f"No Table {table} model definition was found.")
    session.close()
