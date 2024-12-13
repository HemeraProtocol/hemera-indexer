import click


def log_setting(commands):
    commands = click.option(
        "--log-file",
        default=None,
        show_default=True,
        type=str,
        envvar="LOG_FILE",
        help="Log file",
    )(commands)

    commands = click.option(
        "--log-level",
        default="INFO",
        show_default=True,
        type=str,
        envvar="LOG_LEVEL",
        help="Set the logging output level.",
    )(commands)

    return commands
