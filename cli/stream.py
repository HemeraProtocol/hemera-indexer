import logging
import os
import time

import click
from web3 import Web3

from cli.logo import print_logo
from common.services.postgresql_service import PostgreSQLService
from enumeration.entity_type import DEFAULT_COLLECTION, calculate_entity_value, generate_output_types
from indexer.controller.scheduler.job_scheduler import JobScheduler
from indexer.controller.stream_controller import StreamController
from indexer.exporters.item_exporter import create_item_exporters
from indexer.utils.exception_recorder import ExceptionRecorder
from indexer.utils.limit_reader import create_limit_reader
from indexer.utils.logging_utils import configure_logging, configure_signals
from indexer.utils.parameter_utils import (
    check_file_exporter_parameter,
    check_source_load_parameter,
    generate_dataclass_type_list_from_parameter,
)
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
    default="https://ethereum-rpc.publicnode.com",
    show_default=True,
    type=str,
    envvar="PROVIDER_URI",
    help="The URI of the web3 provider e.g. "
    "file://$HOME/Library/Ethereum/geth.ipc or https://ethereum-rpc.publicnode.com",
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
    default="https://ethereum-rpc.publicnode.com",
    show_default=True,
    type=str,
    envvar="DEBUG_PROVIDER_URI",
    help="The URI of the web3 debug provider e.g. "
    "file://$HOME/Library/Ethereum/geth.ipc or https://ethereum-rpc.publicnode.com",
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
    show_default=True,
    type=int,
    help="Start block",
    envvar="START_BLOCK",
)
@click.option(
    "-e",
    "--end-block",
    default=None,
    show_default=True,
    type=int,
    help="End block",
    envvar="END_BLOCK",
)
@click.option(
    "--retry-from-record",
    default=True,
    show_default=True,
    type=bool,
    envvar="RETRY_FROM_RECORD",
    help="With the default parameter, the program will always run from the -s parameter, "
    "and when set to True, it will run from the record point between -s and -e",
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
    default=2,
    show_default=True,
    type=float,
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
    help="The number of workers during a request to rpc.",
    envvar="MAX_WORKERS",
)
@click.option(
    "-pn",
    "--process-numbers",
    default=1,
    show_default=True,
    type=int,
    help="The processor numbers to ues.",
    envvar="PROCESS_NUMBERS",
)
@click.option(
    "-ps",
    "--process-size",
    default=None,
    show_default=True,
    type=int,
    help="The data size for every process to handle. Default to {B}/{pn} ,see above",
    envvar="PROCESS_SIZE",
)
@click.option(
    "-pto",
    "--process-time-out",
    default=None,
    show_default=True,
    type=int,
    help="Timeout for every processor, default to {ps} * 300 , see above",
    envvar="PROCESS_TIME_OUT",
)
@click.option(
    "--delay",
    default=0,
    show_default=True,
    type=int,
    envvar="DELAY",
    help="The limit number of blocks which delays from the network current block number.",
)
@click.option(
    "--source-path",
    default=None,
    show_default=True,
    required=False,
    type=str,
    envvar="SOURCE_PATH",
    help="The path to load the data."
    "Load from local csv file e.g. csvfile://your-file-direction; "
    "or local json file e.g. jsonfile://your-file-direction; ",
)
@click.option(
    "--source-types",
    default="block,transaction,log",
    show_default=True,
    type=str,
    envvar="SOURCE_TYPES",
    help="The list of types to read from source, corresponding to more detailed data models. "
    "Examples include: block, transaction, log, "
    "token, address_token_balance, erc20_token_transfer, erc721_token_transfer, erc1155_token_transfer, "
    "trace, contract, coin_balance.",
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
    default="file:sync_record",
    show_default=True,
    type=str,
    envvar="SYNC_RECORDER",
    help="How to store the sync record data."
    'e.g pg:base. means sync record data will store in pg as "base" be key'
    'or file:base. means sync record data will store in file as "base" be file name',
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
    "-m",
    "--multicall",
    default=False,
    show_default=True,
    type=bool,
    help="if `multicall` is set to True, it will decrease the consume of rpc calls",
    envvar="MULTI_CALL_ENABLE",
)
@click.option(
    "--auto-reorg",
    default=False,
    show_default=True,
    type=bool,
    envvar="AUTO_REORG",
    help="Whether to detect reorg in data streams and automatically repair data.",
)
@click.option(
    "--config-file",
    default=None,
    show_default=True,
    type=str,
    envvar="CONFIG_FILE",
    help="The path to the configuration file, if provided, the configuration file will be used to load the configuration. Supported formats are json and yaml.",
)
@click.option(
    "--force-filter-mode",
    default=False,
    show_default=True,
    type=bool,
    envvar="FORCE_FILTER_MODE",
    help="Force the filter mode to be enabled, even if no filters job are provided.",
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
def stream(
    provider_uri,
    debug_provider_uri,
    postgres_url,
    output,
    db_version,
    start_block,
    end_block,
    entity_types,
    output_types,
    source_types,
    blocks_per_file,
    delay=0,
    period_seconds=10,
    batch_size=10,
    debug_batch_size=1,
    block_batch_size=1,
    max_workers=5,
    process_numbers=1,
    process_size=None,
    process_time_out=None,
    log_file=None,
    pid_file=None,
    source_path=None,
    sync_recorder="file:sync_record",
    retry_from_record=False,
    cache="memory",
    auto_reorg=False,
    multicall=True,
    config_file=None,
    force_filter_mode=False,
    auto_upgrade_db=True,
    log_level="INFO",
):
    print_logo()
    configure_logging(log_level, log_file)
    configure_signals()
    provider_uri = pick_random_provider_uri(provider_uri)
    debug_provider_uri = pick_random_provider_uri(debug_provider_uri)
    logging.getLogger("ROOT").info("Using provider " + provider_uri)
    logging.getLogger("ROOT").info("Using debug provider " + debug_provider_uri)

    # parameter logic checking
    if source_path:
        check_source_load_parameter(source_path, start_block, end_block, auto_reorg)
    check_file_exporter_parameter(output, block_batch_size, blocks_per_file)

    # build config
    config = {
        "blocks_per_file": blocks_per_file,
        "source_path": source_path,
        "chain_id": Web3(Web3.HTTPProvider(provider_uri)).eth.chain_id,
    }

    if postgres_url:
        service = PostgreSQLService(postgres_url, db_version=db_version, init_schema=auto_upgrade_db)
        config["db_service"] = service
        exception_recorder.init_pg_service(service)
    else:
        logging.getLogger("ROOT").warning("No postgres url provided. Exception recorder will not be useful.")

    if config_file:
        file_based_config = {}
        if not os.path.exists(config_file):
            raise click.ClickException(f"Config file {config_file} not found")
        with open(config_file, "r") as f:
            if config_file.endswith(".json"):
                import json

                file_based_config = json.load(f)
            elif config_file.endswith(".yaml") or config_file.endswith(".yml"):
                import yaml

                file_based_config = yaml.safe_load(f)
            else:
                raise click.ClickException(f"Config file {config_file} is not supported)")

        if file_based_config.get("chain_id") != config["chain_id"]:
            raise click.ClickException(
                f"Config file {config_file} is not compatible with chain_id {config['chain_id']}"
            )
        else:
            logging.getLogger("ROOT").info(f"Loading config from file: {config_file}, chain_id: {config['chain_id']}")
            config.update(file_based_config)
    output_types_by_entity_type = []
    if entity_types is not None:
        entity_types = calculate_entity_value(entity_types)
        output_types_by_entity_type = list(set(generate_output_types(entity_types)))

    output_types = list(
        set(generate_dataclass_type_list_from_parameter(output_types, "output") + output_types_by_entity_type)
    )

    if source_path and source_path.startswith("postgresql://"):
        source_types = generate_dataclass_type_list_from_parameter(source_types, "source")

    job_scheduler = JobScheduler(
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(lambda: get_provider_from_uri(debug_provider_uri, batch=True)),
        batch_size=batch_size,
        debug_batch_size=debug_batch_size,
        max_workers=max_workers,
        config=config,
        required_output_types=output_types,
        required_source_types=source_types,
        cache=cache,
        auto_reorg=auto_reorg,
        multicall=multicall,
        force_filter_mode=force_filter_mode,
    )

    if process_numbers is None:
        process_numbers = 1
    if process_size is None:
        process_size = int(block_batch_size / process_numbers)
    if process_time_out is None:
        process_time_out = 300 * process_size

    controller = StreamController(
        job_scheduler=job_scheduler,
        sync_recorder=create_recorder(sync_recorder, config),
        item_exporters=create_item_exporters(output, config),
        required_output_types=output_types,
        limit_reader=create_limit_reader(
            source_path, ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=False))
        ),
        retry_from_record=retry_from_record,
        delay=delay,
        process_numbers=process_numbers,
        process_size=process_size,
        process_time_out=process_time_out,
    )

    controller.action(
        start_block=start_block,
        end_block=end_block,
        block_batch_size=block_batch_size,
        period_seconds=period_seconds,
        pid_file=pid_file,
    )
