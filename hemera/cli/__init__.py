import click

from hemera.cli.api import api
from hemera.cli.db import db
from hemera.cli.reorg import reorg
from hemera.cli.stream import stream
from hemera.indexer.utils.logging_utils import logging_basic_config

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
cli.add_command(reorg, "reorg")
cli.add_command(db, "db")
