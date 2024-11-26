import os
import sys
from datetime import datetime

import click
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from indexer.schedule_jobs.aggregates_jobs import aggregates_yesterday_job, aggregates_current_date_job


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
@click.option(
    "-cf",
    "--config-file",
    default=None,
    show_default=True,
    type=str,
    envvar="CONFIG_FILE",
    help="",
)
def schedule(chain_name: str, postgres_url: str, dblink_url: str, config_file) -> None:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)  # Line-buffered stdout
    sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)  # Line-buffered stderr

    # Can be passed from outside in the form of crontab
    hour = 1
    minute = 0

    scheduler = BlockingScheduler()
    job_args = (chain_name, postgres_url, dblink_url, config_file)
    scheduler.add_job(aggregates_yesterday_job, 'cron', hour=hour, minute=minute, args=job_args)

    current_crontab_time = "0 6,12,18 * * *"

    trigger = CronTrigger.from_crontab(current_crontab_time)
    scheduler.add_job(func=aggregates_current_date_job, trigger=trigger, args=job_args)

    scheduler.start()
