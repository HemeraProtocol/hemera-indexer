import logging

import click
from controller.dispatcher.stream_dispatcher import StreamDispatcher
from controller.stream_controller import StreamController
from enumeration.entity_type import calculate_entity_value
from exporters.jdbc.postgresql_service import PostgreSQLService
from utils.logging_utils import configure_signals, configure_logging
from utils.provider import get_provider_from_uri
from exporters.item_exporter import create_item_exporters
from utils.thread_local_proxy import ThreadLocalProxy
from utils.utils import pick_random_provider_uri, extract_url_from_output


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-p', '--provider-uri', default='https://mainnet.infura.io', show_default=True, type=str,
              help='The URI of the web3 provider e.g. '
                   'file://$HOME/Library/Ethereum/geth.ipc or https://mainnet.infura.io')
@click.option('-d', '--debug-provider-uri', default='https://mainnet.infura.io', show_default=True, type=str,
              help='The URI of the web3 debug provider e.g. '
                   'file://$HOME/Library/Ethereum/geth.ipc or https://mainnet.infura.io')
@click.option('-o', '--output', type=str,
              help='Either Google PubSub topic path e.g. projects/your-project/topics/crypto_ethereum; '
                   'or Postgres connection url e.g. postgresql+pg8000://postgres:admin@127.0.0.1:5432/ethereum; '
                   'or GCS bucket e.g. gs://your-bucket-name; '
                   'or kafka, output name and connection host:port e.g. kafka/127.0.0.1:9092 '
                   'or Kinesis, e.g. kinesis://your-data-stream-name'
                   'If not specified will print to console')
@click.option('-e', '--entity-types', default=','.join(ALL_ENTITY_COLLECTIONS), show_default=True, type=str,
              help='The list of entity types to export. e.g. block,transaction,log')
@click.option('-v', '--db-version', default="head", show_default=True, type=str,
              help='The database version to initialize the database. using the alembic script\'s revision ID to '
                   'specify a version.'
                   ' e.g. head, indicates the latest version.'
                   'or base, indicates the empty database without any table.')
@click.option('-s', '--start-block', default=None, show_default=True, type=int, help='Start block')
@click.option('--period-seconds', default=10, show_default=True, type=int,
              help='How many seconds to sleep between syncs')
@click.option('-b', '--batch-size', default=10, show_default=True, type=int,
              help='How many blocks to batch in single request')
@click.option('-B', '--block-batch-size', default=1, show_default=True, type=int,
              help='How many blocks to batch in single sync round')
@click.option('-w', '--max-workers', default=5, show_default=True, type=int, help='The number of workers')
def stream(provider_uri, debug_provider_uri, output, db_version, start_block, entity_types, period_seconds=10,
           batch_size=2, block_batch_size=10, max_workers=5, log_file=None, pid_file=None):
    configure_logging(log_file)
    configure_signals()

    provider_uri = pick_random_provider_uri(provider_uri)
    debug_provider_uri = pick_random_provider_uri(debug_provider_uri)
    logging.info('Using provider ' + provider_uri)
    logging.info('Using debug provider ' + debug_provider_uri)

    # build exporter config
    exporter_config = {
        "db_version": db_version,
    }

    # build postgresql service
    service_url = extract_url_from_output(output)
    service = PostgreSQLService(service_url)

    stream_dispatcher = StreamDispatcher(
        service=service,
        batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=True)),
        batch_web3_debug_provider=ThreadLocalProxy(lambda: get_provider_from_uri(debug_provider_uri, batch=True)),
        item_exporter=create_item_exporters(output, exporter_config),
        batch_size=batch_size,
        max_workers=max_workers,
        entity_types=calculate_entity_value(entity_types))

    controller = StreamController(
        service=service,
        batch_web3_provider=ThreadLocalProxy(
            lambda: get_provider_from_uri(provider_uri, batch=True)),
        job_dispatcher=stream_dispatcher,
    )

    controller.action(start_block=start_block, block_batch_size=block_batch_size, period_seconds=period_seconds,
                      pid_file=pid_file)
