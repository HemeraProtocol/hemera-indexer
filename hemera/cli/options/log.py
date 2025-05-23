import click


def log_setting(options):
    options = click.option(
        "--log-file",
        default=None,
        show_default=True,
        type=str,
        envvar="LOG_FILE",
        help="Log file",
    )(options)

    options = click.option(
        "--log-level",
        default="INFO",
        show_default=True,
        type=str,
        envvar="LOG_LEVEL",
        help="Set the logging output level.",
    )(options)

    return options
