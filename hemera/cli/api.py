import click
import uvicorn

from hemera.app.main import app
from hemera.common.logo import print_logo


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
def api():
    print_logo()

    uvicorn.run(app, host="0.0.0.0", port=8082)
