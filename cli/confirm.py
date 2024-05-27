import logging
from datetime import datetime, timezone, timedelta

import click

from exporters.jdbc.postgresql_service import PostgreSQLService
from exporters.jdbc.schema.block_timestamp_mapper import BlockTimestampMapper
from jobs.export_and_confirm_all import confirm_all
from utils.streaming.streaming_utils import configure_signals, configure_logging

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
              help='Either file system path e.g. file://projects/your-project/topics/crypto_ethereum; '
                   'or Postgres connection url e.g. postgresql+pg8000://postgres:admin@127.0.0.1:5432/ethereum; '
                   'If not specified will print to console')
@click.option('-v', '--db-version', default="head", show_default=True, type=str,
              help='The database version to initialize the database. using the alembic script\'s revision ID to '
                   'specify a version.'
                   ' e.g. head, indicates the latest version.'
                   'or base, indicates the empty database without any table.')
@click.option('-s', '--start-time', default=None, required=True, type=str,
              help='Specify the start time of range for data confirming. e.g. 2024-01-01_00:00:00')
@click.option('-b', '--partition-batch-size', default=10000, show_default=True, type=int,
              help='The number of blocks to export in partition.')
@click.option('-B', '--export-batch-size', default=1, show_default=True, type=int,
              help='How many blocks to batch in single sync round')
@click.option('-w', '--max-workers', default=5, show_default=True, type=int, help='The number of workers')
@click.option('--log-file', default=None, show_default=True, type=str, help='Log file')
def confirm(provider_uri, debug_provider_uri, output, db_version, start_time,
            partition_batch_size=10000, export_batch_size=10, max_workers=5, log_file=None):
    configure_logging(log_file)
    configure_signals()

    provider_uri = pick_random_provider_uri(provider_uri)
    debug_provider_uri = pick_random_provider_uri(debug_provider_uri)
    logging.info('Using provider ' + provider_uri)
    logging.info('Using debug provider ' + debug_provider_uri)

    start_time, end_time = is_valid_export_time_format(start_time)
    start_str = start_time.strftime('%Y-%m-%d_%H:%M:%S')
    end_str = end_time.strftime('%Y-%m-%d_%H:%M:%S')
    start_ts = int(start_time.timestamp())
    end_ts = int(end_time.timestamp())
    logging.info(f'Confirm blocks datetime between {start_str} and {end_str}')

    # build postgresql service, check the block number by timestamp
    service_url = extract_url_from_output(output)
    service = PostgreSQLService(service_url)
    start_block = get_block_number_from_timestamp(service.get_service_session(), start_ts)
    end_block = get_block_number_from_timestamp(service.get_service_session(), end_ts)

    if start_block is None or end_block is None:
        raise ValueError("start time or end time indicate invalid block number")

    logging.info(f'Confirm blocks number between {start_block} and {end_block}')

    # build exporter config
    exporter_config = {
        "db_version": db_version,
        "confirm": True,
        "partition_size": partition_batch_size,
        "time_range": f"{start_str}"
    }

    confirm_all(start_block=start_block,
                end_block=end_block - 1,
                batch_web3_provider=ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=True)),
                batch_web3_debug_provider=ThreadLocalProxy(lambda: get_provider_from_uri(provider_uri, batch=True)),
                item_exporter=create_item_exporters(output, exporter_config),
                export_batch_size=export_batch_size,
                max_workers=max_workers)


def is_valid_export_time_format(time):
    valid_format = "%Y-%m-%d_%H:00:00"
    try:
        start_dt = datetime.strptime(time, valid_format).replace(tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(hours=1)
    except ValueError:
        raise ValueError("The start time of range must be YYYY-MM-DD HH:00:00 format")

    return start_dt, end_dt


def get_block_number_from_timestamp(session, timestamp):
    result = session.query(BlockTimestampMapper).filter(BlockTimestampMapper.ts == timestamp).first()
    if result is not None:
        return result.block_number
    return None
