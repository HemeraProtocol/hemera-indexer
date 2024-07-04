import logging

import click
from controller.dispatcher.stream_dispatcher import StreamDispatcher
from controller.stream_controller import StreamController
from enumeration.entity_type import calculate_entity_value, ALL_ENTITY_COLLECTIONS
from exporters.jdbc.postgresql_service import PostgreSQLService
from utils.logging_utils import configure_signals, configure_logging
from utils.provider import get_provider_from_uri
from exporters.item_exporter import create_item_exporters
from utils.thread_local_proxy import ThreadLocalProxy
from utils.utils import pick_random_provider_uri, verify_db_connection_url, set_config


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-p', '--provider-uri', default='https://mainnet.infura.io', show_default=True, type=str,
              envvar='PROVIDER_URI',
              help='The URI of the web3 provider e.g. '
                   'file://$HOME/Library/Ethereum/geth.ipc or https://mainnet.infura.io')
@click.option('-d', '--debug-provider-uri', default='https://mainnet.infura.io', show_default=True, type=str,
              envvar="DEBUG_PROVIDER_URI",
              help='The URI of the web3 debug provider e.g. '
                   'file://$HOME/Library/Ethereum/geth.ipc or https://mainnet.infura.io')
@click.option('-pg', '--postgres-url', type=str, required=True,
              envvar="DATABASE_URL",
              help='The required postgres connection url.'
                   'e.g. postgresql+psycopg2://postgres:admin@127.0.0.1:5432/ethereum')
@click.option('-o', '--output', type=str,
              envvar='OUTPUT',
              help='The extra output selection.'
                   'Print to console e.g. console; '
                   'or local json file e.g. jsonfile://your-file-path; '
                   'or local csv file e.g. csvfile://your-file-path; '
                   'or both. e.g. console,jsonfile://your-file-path,csvfile://your-file-path')
@click.option('-E', '--entity-types', default=','.join(ALL_ENTITY_COLLECTIONS), show_default=True, type=str,
              envvar='ENTITY_TYPES',
              help='The list of entity types to export. e.g. block,transaction,log')
@click.option('-v', '--db-version', default="head", show_default=True, type=str,
              envvar='DB_VERSION',
              help='The database version to initialize the database. using the alembic script\'s revision ID to '
                   'specify a version.'
                   ' e.g. head, indicates the latest version.'
                   'or base, indicates the empty database without any table.')
@click.option('-s', '--start-block', default=None, show_default=True, type=int, help='Start block',
              envvar='START_BLOCK')
@click.option('-e', '--end-block', default=None, show_default=True, type=int, help='end block',
              envvar='END_BLOCK')
@click.option('--partition-size', default=50000, show_default=True, type=int,
              envvar='PARTITION_SIZE',
              help='How many records was written to each file')
@click.option('--period-seconds', default=10, show_default=True, type=int,
              envvar='PERIOD_SECONDS',
              help='How many seconds to sleep between syncs')
@click.option('-b', '--batch-size', default=10, show_default=True, type=int,
              envvar='BATCH_SIZE',
              help='How many parameters to batch in single request')
@click.option('-db', '--debug-batch-size', default=1, show_default=True, type=int,
              envvar='DEBUG_BATCH_SIZE',
              help='How many parameters to batch in single debug rpc request')
@click.option('-B', '--block-batch-size', default=1, show_default=True, type=int,
              envvar='BLOCK_BATCH_SIZE',
              help='How many blocks to batch in single sync round')
@click.option('-w', '--max-workers', default=5, show_default=True, type=int, help='The number of workers',
              envvar='MAX_WORKERS')
@click.option('--log-file', default=None, show_default=True, type=str, envvar='LOG_FILE', help='Log file')
def stream(provider_uri, debug_provider_uri, postgres_url, output, db_version, start_block, end_block, entity_types,
           partition_size, period_seconds=10, batch_size=10, debug_batch_size=1, block_batch_size=1, max_workers=5,
           log_file=None, pid_file=None):
    configure_logging(log_file)
    configure_signals()

    provider_uri = pick_random_provider_uri(provider_uri)
    debug_provider_uri = pick_random_provider_uri(debug_provider_uri)
    logging.info('Using provider ' + provider_uri)
    logging.info('Using debug provider ' + debug_provider_uri)

    # set alembic.ini and build postgresql service
    service_url = verify_db_connection_url(postgres_url)
    if service_url is None:
        raise click.ClickException('postgresql url must be provided.')
    set_config(config_file='alembic.ini', section='alembic', key='sqlalchemy.url', value=service_url)
    service = PostgreSQLService(service_url, db_version=db_version)

    # build exporter config
    exporter_config = {
        "db_service": service,
        "partition_size": partition_size,
    }

    entity_types = calculate_entity_value(entity_types)

    stream_dispatcher = StreamDispatcher(
        service=service,
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(provider_uri, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(debug_provider_uri, batch=True)),
        item_exporter=create_item_exporters(output, exporter_config),
        batch_size=batch_size,
        debug_batch_size=debug_batch_size,
        max_workers=max_workers,
        entity_types=entity_types)

    controller = StreamController(
        service=service,
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(provider_uri, batch=False)),
        entity_types=entity_types,
        job_dispatcher=stream_dispatcher,
    )

    controller.action(start_block=start_block,
                      end_block=end_block,
                      block_batch_size=block_batch_size,
                      period_seconds=period_seconds,
                      pid_file=pid_file)
