import os
import sys
from datetime import datetime

import click
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from common.services.postgresql_service import PostgreSQLService
from indexer.aggr_jobs.aggr_jobs import run_aggregate_job
from indexer.aggr_jobs.utils import DateType, check_data_completeness, get_yesterday_date, read_yaml_file, \
    get_current_date
from indexer.controller.aggregates_controller import AggregatesController
from indexer.controller.dispatcher.aggregates_dispatcher import AggregatesDispatcher


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-cn",
    "--chain-name",
    default=None,
    show_default=True,
    type=str,
    help='The chain name of the chain to aggregate data for',
    envvar="CHAIN_NAME",
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
    "-p",
    "--provider-uri",
    default=None,
    show_default=True,
    type=str,
    envvar="PROVIDER_URI",
    help="The URI of the web3 provider e.g. "
         "file://$HOME/Library/Ethereum/geth.ipc or https://mainnet.infura.io"
         "It helps determine whether the latest synchronized data meets the required execution date range.",
)
@click.option(
    "-sd",
    "--start-date",
    default=None,
    show_default=True,
    type=DateType(),
    help="Start date in YYYY-MM-DD format",
    envvar="START_DATE",
)
@click.option(
    "-ed",
    "--end-date",
    default=None,
    show_default=True,
    type=DateType(),
    help="End date in YYYY-MM-DD format",
    envvar="END_DATE",
)
@click.option(
    "-D",
    "--date-batch-size",
    default=5,
    show_default=True,
    type=int,
    envvar="DATE_BATCH_SIZE",
    help="How many DATEs to batch in single sync round",
)
@click.option(
    "-cf",
    "--config-file",
    default=None,
    show_default=True,
    type=str,
    envvar="CONFIG_FILE",
    help="",
)
def aggregates(chain_name, postgres_url, provider_uri, start_date, end_date, date_batch_size, config_file):
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)  # Line-buffered stdout
    sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)  # Line-buffered stderr

    file = read_yaml_file(config_file)
    schedule_dict = file.get('schedule')
    if schedule_dict:
        scheduler = BlockingScheduler()
        for day_str, crontab in schedule_dict.items():
            if day_str == 'today':
                start_date, end_date = get_current_date()
            elif day_str == 'yesterday':
                start_date, end_date = get_yesterday_date()

            job_args = (chain_name, postgres_url, start_date, end_date)
            trigger = CronTrigger.from_crontab(crontab)
            scheduler.add_job(func=run_aggregate_job, trigger=trigger, args=job_args)
        scheduler.start()

    else:
        if not start_date and not end_date:
            start_date, end_date = get_yesterday_date()
        elif not end_date:
            _, end_date = get_yesterday_date()

        run_aggregate_job(chain_name, postgres_url, start_date, end_date)
