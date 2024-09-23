import click

from common.services.postgresql_service import PostgreSQLService


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-pg",
    "--postgres-url",
    type=str,
    required=False,
    envvar="POSTGRES_URL",
    help="The required postgres connection url." "e.g. postgresql+psycopg2://postgres:admin@127.0.0.1:5432/ethereum",
)
def stream(postgres_url):
    PostgreSQLService(postgres_url, db_version="head", init_schema=True)
