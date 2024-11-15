import logging
import os

import click

from common.services.postgresql_service import PostgreSQLService
from enumeration.entity_type import ALL_ENTITY_COLLECTIONS, calculate_entity_value, generate_output_types
from indexer.controller.reorg_controller import ReorgController
from indexer.controller.scheduler.reorg_scheduler import ReorgScheduler
from indexer.exporters.postgres_item_exporter import PostgresItemExporter
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.logging_utils import configure_logging, configure_signals
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.rpc_utils import pick_random_provider_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy

# exception_recorder = ExceptionRecorder()


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-p",
    "--provider-uri",
    default="https://ethereum-rpc.publicnode.com",
    show_default=True,
    type=str,
    envvar="PROVIDER_URI",
    help="The URI of the web3 provider e.g. "
    "file://$HOME/Library/Ethereum/geth.ipc or https://ethereum-rpc.publicnode.com",
)
@click.option(
    "-d",
    "--debug-provider-uri",
    default="https://ethereum-rpc.publicnode.com",
    show_default=True,
    type=str,
    envvar="DEBUG_PROVIDER_URI",
    help="The URI of the web3 debug provider e.g. "
    "file://$HOME/Library/Ethereum/geth.ipc or https://ethereum-rpc.publicnode.com",
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
    "--debug-batch-size",
    default=1,
    show_default=True,
    type=int,
    envvar="DEBUG_BATCH_SIZE",
    help="How many parameters to batch in single debug rpc request",
)
@click.option(
    "--block-number",
    show_default=True,
    type=int,
    envvar="BLOCK_NUMBER",
    help="Specify the block number to reorging.",
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
@click.option(
    "-m",
    "--multicall",
    default=False,
    show_default=True,
    type=bool,
    help="if `multicall` is set to True, it will decrease the consume of rpc calls",
    envvar="MULTI_CALL_ENABLE",
)
@click.option("--cache", default=None, show_default=True, type=str, envvar="CACHE", help="Cache")
@click.option(
    "--auto-upgrade-db",
    default=True,
    show_default=True,
    type=bool,
    envvar="AUTO_UPGRADE_DB",
    help="Whether to automatically run database migration scripts to update the database to the latest version.",
)
@click.option(
    "--log-level",
    default="INFO",
    show_default=True,
    type=str,
    envvar="LOG_LEVEL",
    help="Set the logging output level.",
)
def reorg(
    provider_uri,
    debug_provider_uri,
    postgres_url,
    block_number,
    ranges,
    batch_size,
    debug_batch_size,
    db_version="head",
    multicall=True,
    log_file=None,
    cache=None,
    config_file=None,
    auto_upgrade_db=True,
    log_level="INFO",
):
    configure_logging(log_level=log_level, log_file=log_file)
    configure_signals()

    provider_uri = pick_random_provider_uri(provider_uri)
    debug_provider_uri = pick_random_provider_uri(debug_provider_uri)
    logging.info("Using provider " + provider_uri)
    logging.info("Using debug provider " + debug_provider_uri)

    # build postgresql service
    if postgres_url:
        service = PostgreSQLService(postgres_url, db_version=db_version, init_schema=auto_upgrade_db)
        config = {"db_service": service}
        # exception_recorder.init_pg_service(service)
    else:
        logging.error("No postgres url provided. Exception recorder will not be useful.")
        exit(1)

    if config_file:
        if not os.path.exists(config_file):
            raise click.ClickException(f"Config file {config_file} not found")
        with open(config_file, "r") as f:
            if config_file.endswith(".json"):
                import json

                config.update(json.load(f))
            elif config_file.endswith(".yaml") or config_file.endswith(".yml"):
                import yaml

                config.update(yaml.safe_load(f))
            else:
                raise click.ClickException(f"Config file {config_file} is not supported)")

    entity_types = calculate_entity_value(",".join(ALL_ENTITY_COLLECTIONS))
    output_types = list(generate_output_types(entity_types))

    job_scheduler = ReorgScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(lambda: get_provider_from_uri(debug_provider_uri, batch=True)),
        item_exporters=PostgresItemExporter(postgres_url=postgres_url, db_version=db_version, init_schema=auto_upgrade_db),
        batch_size=batch_size,
        debug_batch_size=debug_batch_size,
        required_output_types=output_types,
        config=config,
        cache=cache,
        multicall=multicall,
    )

    controller = ReorgController(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=False)),
        job_scheduler=job_scheduler,
        ranges=ranges,
        config=config,
    )

    job = None
    while True:
        if job:
            controller.action(
                job_id=job.job_id,
                block_number=job.last_fixed_block_number - 1,
                remains=job.remain_process,
            )
        else:
            controller.action(block_number=block_number)

        job = controller.wake_up_next_job()
        if job:
            logging.info(f"Waking up uncompleted job: {job.job_id}.")
        else:
            logging.info("No more uncompleted jobs to wake-up, reorg process will terminate.")
            break
