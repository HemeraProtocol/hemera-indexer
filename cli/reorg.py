import logging

import click

from common.services.postgresql_service import PostgreSQLService
from enumeration.entity_type import calculate_entity_value, generate_output_types, ALL_ENTITY_COLLECTIONS
from enumeration.schedule_mode import ScheduleMode
from indexer.controller.reorg_controller import ReorgController
from indexer.exporters.postgres_item_exporter import PostgresItemExporter
from indexer.jobs.job_scheduler import JobScheduler
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.logging_utils import configure_logging, configure_signals
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy
from indexer.utils.utils import pick_random_provider_uri

exception_recorder = ExceptionRecorder()


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-p",
    "--provider-uri",
    default="https://mainnet.infura.io",
    show_default=True,
    type=str,
    envvar="PROVIDER_URI",
    help="The URI of the web3 provider e.g. " "file://$HOME/Library/Ethereum/geth.ipc or https://mainnet.infura.io",
)
@click.option(
    "-d",
    "--debug-provider-uri",
    default="https://mainnet.infura.io",
    show_default=True,
    type=str,
    envvar="DEBUG_PROVIDER_URI",
    help="The URI of the web3 debug provider e.g. "
         "file://$HOME/Library/Ethereum/geth.ipc or https://mainnet.infura.io",
)
@click.option(
    "-pg",
    "--postgres-url",
    type=str,
    required=True,
    envvar="POSTGRES_URL",
    help="The required postgres connection url." "e.g. postgresql+psycopg2://postgres:admin@127.0.0.1:5432/ethereum",
)
@click.option(
    "-v",
    "--db-version",
    default="head",
    show_default=True,
    type=str,
    envvar="DB_VERSION",
    help="The database version to initialize the database. using the alembic script's revision ID to "
         "specify a version."
         " e.g. head, indicates the latest version."
         "or base, indicates the empty database without any table.",
)
@click.option(
    "-b",
    "--batch-size",
    default=10,
    show_default=True,
    type=int,
    envvar="BATCH_SIZE",
    help="How many parameters to batch in single request",
)
@click.option(
    "-db",
    "--debug-batch-size",
    default=1,
    show_default=True,
    type=int,
    envvar="DEBUG_BATCH_SIZE",
    help="How many parameters to batch in single debug rpc request",
)
@click.option(
    "-r",
    "--ranges",
    default=1000,
    show_default=True,
    type=int,
    envvar="RANGES",
    help="Specify the range limit for data fixing.",
)
@click.option(
    "--log-file",
    default=None,
    show_default=True,
    type=str,
    envvar="LOG_FILE",
    help="Log file",
)
@click.option("--cache", default=None, show_default=True, type=str, envvar="CACHE", help="Cache")
def reorg(
        provider_uri,
        debug_provider_uri,
        postgres_url,
        db_version,
        block_number,
        ranges,
        batch_size,
        debug_batch_size,
        log_file=None,
        cache=None,
):
    configure_logging(log_file)
    configure_signals()

    provider_uri = pick_random_provider_uri(provider_uri)
    debug_provider_uri = pick_random_provider_uri(debug_provider_uri)
    logging.info("Using provider " + provider_uri)
    logging.info("Using debug provider " + debug_provider_uri)

    # build postgresql service
    if postgres_url:
        service = PostgreSQLService(postgres_url, db_version=db_version)
        config = {
            "db_service": service
        }
        exception_recorder.init_pg_service(service)
    else:
        logging.error("No postgres url provided. Exception recorder will not be useful.")
        exit(1)

    entity_types = calculate_entity_value(','.join(ALL_ENTITY_COLLECTIONS))
    output_types = list(generate_output_types(entity_types))

    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(lambda: get_provider_from_uri(debug_provider_uri, batch=True)),
        item_exporters=PostgresItemExporter(config["db_service"]),
        batch_size=batch_size,
        debug_batch_size=debug_batch_size,
        required_output_types=output_types,
        schedule_mode=ScheduleMode.REORG,
        config=config,
        cache=cache,
    )

    controller = ReorgController(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=True)),
        job_scheduler=job_scheduler,
        ranges=ranges,
        config=config,
    )

    controller.action(block_number=block_number)
