from pathlib import Path

import click

from cli.aggregates import aggregates
from cli.api import api
from cli.reorg import reorg
from cli.stream import stream
from indexer.utils.logging_utils import logging_basic_config

logging_basic_config()

from importlib import metadata


def get_version():
    return metadata.version("hemera")


@click.group()
@click.version_option(version=get_version())
@click.pass_context
def cli(ctx):
    pass


cli.add_command(stream, "stream")
cli.add_command(api, "api")
cli.add_command(aggregates, "aggregates")
cli.add_command(reorg, "reorg")
