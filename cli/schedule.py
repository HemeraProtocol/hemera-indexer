import os
import sys
from datetime import datetime

import click
from apscheduler.schedulers.blocking import BlockingScheduler

from indexer.schedule_jobs.aggregates_jobs import aggregates_yesterday_job


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
    "-du",
    "--dblink-url",
    default=None,
    show_default=True,
    type=str,
    envvar="DBLINK_URL",
    help="dblink to take token price, maybe moved to other replace later",
)
def schedule(chain_name: str, postgres_url: str, dblink_url: str) -> None:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)  # Line-buffered stdout
    sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)  # Line-buffered stderr

    # may be can
    hour = 9
    minute = 0

    scheduler = BlockingScheduler()
    job_args = (chain_name, postgres_url, dblink_url)
    scheduler.add_job(aggregates_yesterday_job, 'cron', hour=hour, minute=minute, args=job_args)

    scheduler.start()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'Job started {current_time}, schedule time is {hour}:{minute} daily')
