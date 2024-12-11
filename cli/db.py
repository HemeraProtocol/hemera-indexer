import logging
from typing import List

import click

from common.models import HemeraModel, model_path_patterns
from common.services.postgresql_service import PostgreSQLService
from common.utils.module_loading import import_string, scan_subclass_by_path_patterns

logger = logging.getLogger("DB Client")


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-pg",
    "--postgres-url",
    type=str,
    required=True,
    envvar="POSTGRES_URL",
    help="The required postgres connection url." "e.g. postgresql+psycopg2://postgres:admin@127.0.0.1:5432/ethereum",
)
@click.option(
    "-i",
    "--init",
    is_flag=True,
    required=False,
    help="The -i or --init flag triggers the database initialization process. ",
)
@click.option(
    "-v",
    "--version",
    type=str,
    default="head",
    show_default=True,
    required=False,
    help="The database version that would be initialized. "
    "By using default value 'head', database would be initialized to the latest version."
    "To make this option work, either -i or --init must be used.",
)
@click.option(
    "-c",
    "--create-tables",
    type=str,
    default="",
    required=False,
    help="Table names that need to be created in the database. e.g. blocks,transactions",
)
@click.option(
    "-d",
    "--drop-tables",
    type=str,
    default="",
    required=False,
    help="Table names that need to be dropped in the database. e.g. blocks,transactions",
)
def db(postgres_url, init, version, create_tables="", drop_tables=""):
    service = PostgreSQLService(jdbc_url=postgres_url, db_version=version, init_schema=init)

    if create_tables != "" or drop_tables != "":
        exist_models_path = [
            value["cls_import_path"]
            for key, value in scan_subclass_by_path_patterns(model_path_patterns, HemeraModel).items()
        ]
        exist_models = {
            table.__tablename__: table
            for table in [import_string(path) for path in exist_models_path]
            if hasattr(table, "__tablename__")
        }

        tables = create_tables.split(",")
        if len(tables) > 0:
            create(service, tables, exist_models)

        logger.info("Table creation has been finished.")

        tables = drop_tables.split(",")
        if len(drop_tables) > 0:
            drop(service, tables, exist_models)

        logger.info("Table deletion has been finished.")

    logger.info("db operation finished, now exit.")


def create(service: PostgreSQLService, tables: List[str], exist_models: dict):
    engine = service.get_service_engine()
    for table in tables:
        if table in exist_models:
            exist_models[table].__table__.create(engine, checkfirst=True)
            logger.info(f"Table {table} created successfully.")
        else:
            logger.warning(
                f"No Table {table} model definition was found in the following directories: {model_path_patterns} "
            )


def drop(service: PostgreSQLService, tables: List[str], exist_models: dict):
    engine = service.get_service_engine()
    for table in tables:
        if table in exist_models:
            exist_models[table].__table__.drop(engine, checkfirst=True)
            logger.info(f"Table {table} dropped successfully.")
        else:
            logger.warning(
                f"No Table {table} model definition was found in the following directories: {model_path_patterns} "
            )
