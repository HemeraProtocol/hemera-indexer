import click

from hemera.cli.api import api
from hemera.cli.async_stream import async_stream
from hemera.cli.backtest import backtest
from hemera.cli.db import db
from hemera.cli.init import init
from hemera.cli.reorg import reorg
from hemera.cli.stream import stream
from hemera.common.utils.config import check_and_set_default_env
from hemera.indexer.utils.logging_utils import logging_basic_config

logging_basic_config()

from importlib import metadata


def get_version():
    return metadata.version("hemera")


def load_environ():
    # Job control
    check_and_set_default_env("JOB_RETRIES", "5")
    check_and_set_default_env("PGSOURCE_ACCURACY", "false")

    # Postgres commit control
    check_and_set_default_env("COMMIT_BATCH_SIZE", "1000")

    # BufferService control
    check_and_set_default_env("BUFFER_BLOCK_SIZE", "1")
    check_and_set_default_env("MAX_BUFFER_SIZE", "1")
    check_and_set_default_env("ASYNC_SUBMIT", "false")
    check_and_set_default_env("CONCURRENT_SUBMITTERS", "1")
    check_and_set_default_env("CRASH_INSTANTLY", "true")
    check_and_set_default_env("EXPORT_STRATEGY", "{}")

    # Multicall control
    check_and_set_default_env("GAS_LIMIT", "5000000")
    check_and_set_default_env("BATCH_SIZE", "250")
    check_and_set_default_env("CALLS_LIMIT", "2000")
    check_and_set_default_env("DEFAULT_MULTICALL_ADDRESS", "0xcA11bde05977b3631167028862bE2a173976CA11")

    # MetricsCollector control
    check_and_set_default_env("METRICS_CLIENT_PORT", "9200")


@click.group()
@click.version_option(version=get_version())
@click.pass_context
def cli(ctx):
    load_environ()


cli.add_command(backtest, "backtest")
cli.add_command(stream, "stream")
cli.add_command(async_stream, "async_stream")
cli.add_command(api, "api")
cli.add_command(reorg, "reorg")
cli.add_command(db, "db")
cli.add_command(init, "init")
