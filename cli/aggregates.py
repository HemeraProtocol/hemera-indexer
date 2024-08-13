import click

from common.services.postgresql_service import PostgreSQLService
from indexer.aggr_jobs.utils import DateType, check_data_completeness, get_yesterday_date
from indexer.controller.aggregates_controller import AggregatesController
from indexer.controller.dispatcher.aggregates_dispatcher import AggregatesDispatcher


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
def aggregates(postgres_url, start_date, end_date, date_batch_size):
    if not start_date and not end_date:
        start_date, end_date = get_yesterday_date()
    elif not end_date:
        _, end_date = get_yesterday_date()

    data_completeness = check_data_completeness(start_date, end_date)

    if not data_completeness:
        raise click.ClickException("Data must be completeness")

    db_service = PostgreSQLService(postgres_url)

    config = {"db_service": db_service}
    dispatcher = AggregatesDispatcher(config)

    controller = AggregatesController(job_dispatcher=dispatcher)
    controller.action(start_date, end_date, date_batch_size)
