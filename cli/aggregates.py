import click

from common.services.postgresql_service import PostgreSQLService
from indexer.aggr_jobs.utils import DateType, check_data_completeness, get_yesterday_date
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
    "-du",
    "--dblink-url",
    default=None,
    show_default=True,
    type=str,
    envvar="DBLINK_URL",
    help="dblink to take token price, maybe moved to other replace later",
)
def aggregates(chain_name, postgres_url, provider_uri, start_date, end_date, date_batch_size, dblink_url):
    if not start_date and not end_date:
        start_date, end_date = get_yesterday_date()
    elif not end_date:
        _, end_date = get_yesterday_date()

    db_service = PostgreSQLService(postgres_url)

    # check_data_completeness(db_service, provider_uri, end_date)

    config = {"db_service": db_service, "chain_name": chain_name, 'dblink_url': dblink_url}
    dispatcher = AggregatesDispatcher(config)

    controller = AggregatesController(job_dispatcher=dispatcher)
    controller.action(start_date, end_date, date_batch_size)
