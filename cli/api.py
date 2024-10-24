import click


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
def api():
    from api.app.main import app

    app.run("0.0.0.0", 8082, threaded=True, debug=True)
