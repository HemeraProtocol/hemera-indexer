import logging
import os

import click

from hemera.cli.options.log import log_setting
from hemera.cli.options.performance import single_performance
from hemera.cli.options.rpc import rpc_provider
from hemera.cli.options.schedule import job_config
from hemera.cli.options.storage import cache_target, postgres
from hemera.common.enumeration.entity_type import EntityType, generate_output_types
from hemera.common.logo import print_logo
from hemera.common.services.postgresql_service import PostgreSQLService
from hemera.common.utils.module_loading import import_submodules
from hemera.indexer.controller.reorg_controller import ReorgController
from hemera.indexer.controller.scheduler.reorg_scheduler import ReorgScheduler
from hemera.indexer.exporters.postgres_item_exporter import PostgresItemExporter
from hemera.indexer.utils.exception_recorder import ExceptionRecorder
from hemera.indexer.utils.logging_utils import configure_logging, configure_signals
from hemera.indexer.utils.provider import get_provider_from_uri
from hemera.indexer.utils.rpc_utils import pick_random_provider_uri
from hemera.indexer.utils.thread_local_proxy import ThreadLocalProxy

exception_recorder = ExceptionRecorder()


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@rpc_provider
@job_config
@postgres
@single_performance
@cache_target
@log_setting
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
    default=10,
    show_default=True,
    type=int,
    envvar="RANGES",
    help="Specify the range limit for data fixing.",
)
def reorg(
    provider_uri=None,
    debug_provider_uri=None,
    config_file=None,
    postgres_url=None,
    batch_size=None,
    debug_batch_size=None,
    max_workers=None,
    multicall=True,
    cache=None,
    log_file=None,
    log_level="INFO",
    block_number=None,
    ranges=None,
):
    print_logo()
    import_submodules("hemera_udf")
    configure_logging(log_level=log_level, log_file=log_file)
    configure_signals()

    provider_uri = pick_random_provider_uri(provider_uri)
    debug_provider_uri = pick_random_provider_uri(debug_provider_uri)
    logging.info("Using provider " + provider_uri)
    logging.info("Using debug provider " + debug_provider_uri)

    # build postgresql service
    if postgres_url:
        service = PostgreSQLService(postgres_url)
        config = {"db_service": service}
        exception_recorder.init_pg_service(service)
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

    entity_types = EntityType.combine_all_entity_types()
    output_types = list(generate_output_types(entity_types))

    job_scheduler = ReorgScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(lambda: get_provider_from_uri(debug_provider_uri, batch=True)),
        item_exporters=PostgresItemExporter(postgres_url=postgres_url),
        batch_size=batch_size,
        debug_batch_size=debug_batch_size,
        max_workers=max_workers,
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
