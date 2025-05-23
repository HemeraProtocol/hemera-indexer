import click

from hemera.common.logo import print_logo


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
def api():
    print_logo()
    from hemera.api.app.main import app

    app.run("0.0.0.0", 8082, threaded=True, debug=True, use_reloader=False)
