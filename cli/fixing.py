import logging

import click

from indexer.controller.fixing_controller import FixingController
from common.services.postgresql_service import PostgreSQLService
from indexer.utils.logging_utils import configure_signals, configure_logging

from indexer.utils.provider import get_provider_from_uri
from indexer.utils.thread_local_proxy import ThreadLocalProxy
from indexer.utils.utils import pick_random_provider_uri
from common.utils.config import init_config_setting


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-p', '--provider-uri', default='https://mainnet.infura.io', show_default=True, type=str,
              envvar='PROVIDER_URI',
              help='The URI of the web3 provider e.g. '
                   'file://$HOME/Library/Ethereum/geth.ipc or https://mainnet.infura.io')
@click.option('-d', '--debug-provider-uri', default='https://mainnet.infura.io', show_default=True, type=str,
              envvar='DEBUG_PROVIDER_URI',
              help='The URI of the web3 debug provider e.g. '
                   'file://$HOME/Library/Ethereum/geth.ipc or https://mainnet.infura.io')
@click.option('-pg', '--postgres-url', type=str, required=True,
              envvar="POSTGRES_URL",
              help='The required postgres connection url.'
                   'e.g. postgresql+psycopg2://postgres:admin@127.0.0.1:5432/ethereum')
@click.option('-v', '--db-version', default="head", show_default=True, type=str,
              envvar='DB_VERSION',
              help='The database version to initialize the database. using the alembic script\'s revision ID to '
                   'specify a version.'
                   ' e.g. head, indicates the latest version.'
                   'or base, indicates the empty database without any table.')
@click.option('-b', '--batch-size', default=10, show_default=True, type=int,
              envvar='BATCH_SIZE',
              help='How many parameters to batch in single request')
@click.option('-db', '--debug-batch-size', default=1, show_default=True, type=int,
              envvar='DEBUG_BATCH_SIZE',
              help='How many parameters to batch in single debug rpc request')
@click.option('-r', '--ranges', default=1000, show_default=True, type=int,
              envvar='RANGES',
              help='Specify the range limit for data fixing.')
@click.option('--batch-size', default=10, show_default=True, type=int,
              envvar='BATCH_SIZE',
              help='How many parameters to batch in single request')
@click.option('--log-file', default=None, show_default=True, type=str, envvar='LOG_FILE', help='Log file')
@click.option('--cache', default=None, show_default=True, type=str, envvar='CACHE', help='Cache')
def fixing(provider_uri, debug_provider_uri, postgres_url, db_version, block_number, ranges,
           batch_size, debug_batch_size, log_file=None, cache=None):
    configure_logging(log_file)
    configure_signals()

    provider_uri = pick_random_provider_uri(provider_uri)
    debug_provider_uri = pick_random_provider_uri(debug_provider_uri)
    logging.info('Using provider ' + provider_uri)
    logging.info('Using debug provider ' + debug_provider_uri)

    # build postgresql service
    service_url = verify_db_connection_url(postgres_url)
    init_config_setting(db_url=service_url, rpc_endpoint=provider_uri)
    service = PostgreSQLService(service_url, db_version=db_version)

    controller = FixingController(service=service,
                                  batch_web3_provider=ThreadLocalProxy(
                                      lambda: get_provider_from_uri(provider_uri, batch=batch_size > 1)),
                                  batch_web3_debug_provider=ThreadLocalProxy(
                                      lambda: get_provider_from_uri(debug_provider_uri, batch=debug_batch_size > 1)),
                                  ranges=ranges,
                                  batch_size=batch_size,
                                  debug_batch_size=debug_batch_size)

    controller.action(block_number=block_number)
