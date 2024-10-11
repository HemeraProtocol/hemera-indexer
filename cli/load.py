import logging
import time

import click

from common.services.postgresql_service import PostgreSQLService
from enumeration.entity_type import DEFAULT_COLLECTION, calculate_entity_value, generate_output_types
from indexer.controller.scheduler.job_scheduler import JobScheduler
from indexer.controller.stream_controller import StreamController
from indexer.domain import Domain
from indexer.exporters.item_exporter import create_item_exporters
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.logging_utils import configure_logging, configure_signals
from indexer.utils.parameter_utils import check_file_exporter_parameter, check_file_load_parameter
from indexer.utils.provider import get_provider_from_uri
from indexer.utils.rpc_utils import pick_random_provider_uri
from indexer.utils.sync_recorder import create_recorder
from indexer.utils.thread_local_proxy import ThreadLocalProxy

exception_recorder = ExceptionRecorder()


def calculate_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"function {func.__name__} time: {execution_time:.6f} s")
        return result

    return wrapper


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
    "-pg",
    "--postgres-url",
    type=str,
    required=False,
    envvar="POSTGRES_URL",
    help="The required postgres connection url." "e.g. postgresql+psycopg2://postgres:admin@127.0.0.1:5432/ethereum",
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
    "-o",
    "--output",
    type=str,
    envvar="OUTPUT",
    help="The output selection."
    "Print to console e.g. console; "
    "or postgresql e.g. postgres"
    "or local json file e.g. jsonfile://your-file-path; "
    "or local csv file e.g. csvfile://your-file-path; "
    "or both. e.g. console,jsonfile://your-file-path,csvfile://your-file-path",
)
@click.option(
    "-E",
    "--entity-types",
    default=",".join(DEFAULT_COLLECTION),
    show_default=True,
    type=str,
    envvar="ENTITY_TYPES",
    help="The list of entity types to export. " "e.g. EXPLORER_BASE | EXPLORER_TOKEN | EXPLORER_TRACE",
)
@click.option(
    "-O",
    "--output-types",
    default=None,
    show_default=True,
    type=str,
    envvar="OUTPUT_TYPES",
    help="The list of output types to export, corresponding to more detailed data models. "
    "Specifying this option will prioritize these settings over the entity types specified in -E. "
    "Examples include: block, transaction, log, "
    "token, address_token_balance, erc20_token_transfer, erc721_token_transfer, erc1155_token_transfer, "
    "trace, contract, coin_balance.",
)
@click.option(
    "-v",
    "--db-version",
    default="head",
    show_default=True,
    type=str,
    envvar="DB_VERSION",
    help="The database version to initialize the database. using the alembic script's revision ID to "
    "specify a version. "
    "e.g. head, indicates the latest version."
    "or base, indicates the empty database without any table.",
)
@click.option(
    "-s",
    "--start-block",
    default=None,
    required=True,
    show_default=True,
    type=int,
    help="Start block",
    envvar="START_BLOCK",
)
@click.option(
    "-e",
    "--end-block",
    default=None,
    required=True,
    show_default=True,
    type=int,
    help="End block",
    envvar="END_BLOCK",
)
@click.option(
    "--blocks-per-file",
    default=1000,
    show_default=True,
    type=int,
    envvar="BLOCKS_PER_FILE",
    help="How many blocks data was written to each file",
)
@click.option(
    "--period-seconds",
    default=10,
    show_default=True,
    type=int,
    envvar="PERIOD_SECONDS",
    help="How many seconds to sleep between syncs",
)
@click.option(
    "-b",
    "--batch-size",
    default=10,
    show_default=True,
    type=int,
    envvar="BATCH_SIZE",
    help="The number of non-debug RPC requests to batch in a single request",
)
@click.option(
    "--debug-batch-size",
    default=1,
    show_default=True,
    type=int,
    envvar="DEBUG_BATCH_SIZE",
    help="The number of debug RPC requests to batch in a single request",
)
@click.option(
    "-B",
    "--block-batch-size",
    default=1,
    show_default=True,
    type=int,
    envvar="BLOCK_BATCH_SIZE",
    help="How many blocks to batch in single sync round",
)
@click.option(
    "-w",
    "--max-workers",
    default=5,
    show_default=True,
    type=int,
    help="The number of workers",
    envvar="MAX_WORKERS",
)
@click.option(
    "--source-path",
    default=None,
    show_default=True,
    required=True,
    type=str,
    envvar="SOURCE_PATH",
    help="The path to load the data."
    "Load from local csv file e.g. csvfile://your-file-direction; "
    "or local json file e.g. jsonfile://your-file-direction; ",
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
    "--pid-file",
    default=None,
    show_default=True,
    type=str,
    envvar="PID_FILE",
    help="Pid file",
)
@click.option(
    "--sync-recorder",
    default="file_sync_record",
    show_default=True,
    type=str,
    envvar="SYNC_RECORDER",
    help="How to store the sync record data."
    'e.g pg_base. means sync record data will store in pg as "base" be key'
    'or file_base. means sync record data will store in file as "base" be file name',
)
@click.option(
    "--cache",
    default="memory",
    show_default=True,
    type=str,
    envvar="CACHE_SERVICE",
    help="How to store the cache data."
    "e.g redis. means cache data will store in redis, redis://localhost:6379"
    "or memory. means cache data will store in memory, memory",
)
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
@calculate_execution_time
def load(
    provider_uri,
    debug_provider_uri,
    postgres_url,
    output,
    db_version,
    start_block,
    end_block,
    entity_types,
    output_types,
    blocks_per_file,
    period_seconds=10,
    batch_size=10,
    debug_batch_size=1,
    block_batch_size=1,
    max_workers=5,
    log_file=None,
    pid_file=None,
    source_path=None,
    sync_recorder="file_sync_record",
    cache="memory",
    auto_upgrade_db=True,
    log_level="INFO",
):
    configure_logging(log_level=log_level, log_file=log_file)
    configure_signals()
    provider_uri = pick_random_provider_uri(provider_uri)
    debug_provider_uri = pick_random_provider_uri(debug_provider_uri)
    logging.info("Using provider " + provider_uri)
    logging.info("Using debug provider " + debug_provider_uri)

    # parameter logic checking
    check_file_load_parameter(source_path)
    check_file_exporter_parameter(output, block_batch_size, blocks_per_file)

    # build config
    config = {"blocks_per_file": blocks_per_file, "source_path": source_path}

    if postgres_url:
        service = PostgreSQLService(postgres_url, db_version=db_version, init_schema=auto_upgrade_db)
        config["db_service"] = service
        exception_recorder.init_pg_service(service)
    else:
        logging.warning("No postgres url provided. Exception recorder will not be useful.")

    if output_types is None:
        entity_types = calculate_entity_value(entity_types)
        output_types = list(generate_output_types(entity_types))
    else:
        domain_dict = Domain.get_all_domain_dict()
        parse_output_types = set()

        for output_type in output_types.split(","):
            if output_type not in domain_dict:
                raise click.ClickException(f"Output type {output_type} is not supported")
            parse_output_types.add(domain_dict[output_type])

        if not output_types:
            raise click.ClickException("No output types provided")
        output_types = list(parse_output_types)

    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(lambda: get_provider_from_uri(debug_provider_uri, batch=True)),
        item_exporters=create_item_exporters(output, config),
        batch_size=batch_size,
        debug_batch_size=debug_batch_size,
        max_workers=max_workers,
        config=config,
        required_output_types=output_types,
        cache=cache,
    )

    controller = StreamController(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=False)),
        job_scheduler=job_scheduler,
        sync_recorder=create_recorder(sync_recorder, config),
    )

    controller.action(
        start_block=start_block,
        end_block=end_block,
        block_batch_size=block_batch_size,
        period_seconds=period_seconds,
        pid_file=pid_file,
    )
