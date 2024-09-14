import datetime

import click

from common.services.postgresql_service import PostgreSQLService
from indexer.aggr_jobs.utils import DateType, get_yesterday_date, parse_job_list
from indexer.controller.aggregates_controller import AggregatesController
from indexer.controller.dispatcher.aggregates_dispatcher import AggregatesDispatcher
from indexer.schedule_jobs.aggregates_jobs import parse_aggregate_schedule


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-jn",
    "--job-name",
    default='all',
    show_default=True,
    type=str,
    help="Job list to aggregate data for, e.g. 'all', 'FBTC', 'EXPLORE',  'FBTC,EXPLORE'",
    envvar="JOB_NAME",
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
    default=30,
    show_default=True,
    type=int,
    envvar="DATE_BATCH_SIZE",
    help="How many DATEs to batch in single sync round",
)
@click.option(
    "--config-file",
    default='/app/aggr_schedule_config.yaml',
    show_default=True,
    type=str,
    envvar="CONFIG_FILE",
    help="",
)
def aggregates(job_name, postgres_url, start_date, end_date, date_batch_size, config_file, provider_uri):
    if not start_date and not end_date:
        start_date, end_date = get_yesterday_date()
    elif not end_date:
        _, end_date = get_yesterday_date()

    # check_data_completeness(db_service, provider_uri, end_date)

    db_service = PostgreSQLService(postgres_url)
    version = int(datetime.datetime.now().timestamp())

    config = {"db_service": db_service, 'version': version}

    job_list = parse_job_list(job_name, config_file)
    dispatcher = AggregatesDispatcher(config, job_list)

    controller = AggregatesController(job_dispatcher=dispatcher)
    controller.action(start_date, end_date, date_batch_size)
