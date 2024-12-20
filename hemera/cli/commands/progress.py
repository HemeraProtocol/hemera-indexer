import click


def index_range(commands):
    commands = click.option(
        "-s",
        "--start-block",
        default=None,
        show_default=True,
        type=int,
        help="Start block",
        envvar="START_BLOCK",
    )(commands)

    commands = click.option(
        "-e",
        "--end-block",
        default=None,
        show_default=True,
        type=int,
        help="End block",
        envvar="END_BLOCK",
    )(commands)
    return commands


def index_record(commands):
    commands = click.option(
        "--sync-recorder",
        default="file:sync_record",
        show_default=True,
        type=str,
        envvar="SYNC_RECORDER",
        help="How to store the sync record data."
        'e.g pg:base. means sync record data will store in pg as "base" be key'
        'or file:base. means sync record data will store in file as "base" be file name',
    )(commands)

    commands = click.option(
        "--retry-from-record",
        default=None,
        show_default=True,
        type=bool,
        envvar="RETRY_FROM_RECORD",
        help="With the default parameter, the program will always run from the -s parameter, "
        "and when set to True, it will run from the record point between -s and -e",
    )(commands)

    return commands
