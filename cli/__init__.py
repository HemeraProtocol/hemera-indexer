import click

# from cli.fixing import fixing
from cli.stream import stream
from indexer.utils.logging_utils import logging_basic_config

logging_basic_config()


@click.group()
@click.version_option(version="2.4.2")
@click.pass_context
def cli(ctx):
    pass


cli.add_command(stream, "stream")
# cli.add_command(fixing, "fixing")
