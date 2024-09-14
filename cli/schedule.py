import os
import sys
from datetime import datetime

import click
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from indexer.schedule_jobs.aggregates_jobs import aggregates_yesterday_job, parse_crontab, parse_aggregate_schedule


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-pg",
    "--postgres-url",
    type=str,
    required=True,
    envvar="POSTGRES_URL",
    help="The required postgres connection url." "e.g. postgresql+psycopg2://postgres:admin@127.0.0.1:5432/ethereum",
)
@click.option(
    "--config-file",
    default='/app/aggr_schedule_config.yaml',
    show_default=True,
    type=str,
    envvar="CONFIG_FILE",
    help="",
)
def schedule(postgres_url, configure_file) -> None:
    sys.stdout = os.fdopen(sys.stdout.fileno(), "w", buffering=1)  # Line-buffered stdout
    sys.stderr = os.fdopen(sys.stderr.fileno(), "w", buffering=1)  # Line-buffered stderr

    jobs = parse_aggregate_schedule(configure_file)

    scheduler = BlockingScheduler()

    for job in jobs:
        schedule_time = job["schedule_time"]
        trigger = CronTrigger.from_crontab(schedule_time)

        job_list_generator = job['job_list_generator']

        job_args = (job_list_generator, postgres_url)

        scheduler.add_job(func=aggregates_yesterday_job, trigger=trigger, args=job_args)

    scheduler.start()
