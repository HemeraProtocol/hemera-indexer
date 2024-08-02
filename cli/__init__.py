from pathlib import Path

import click

# from cli.fixing import fixing
from cli.stream import stream
from indexer.utils.logging_utils import logging_basic_config

logging_basic_config()


def get_version():
    version_file = Path(__file__).parent.parent / "VERSION"
    return version_file.read_text().strip()


@click.group()
@click.version_option(version=get_version())
@click.pass_context
def cli(ctx):
    pass


cli.add_command(stream, "stream")
# cli.add_command(fixing, "fixing")
