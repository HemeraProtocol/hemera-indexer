import click


def index_range(options):
    options = click.option(
        "-s",
        "--start-block",
        show_default=True,
        type=int,
        help="Start block",
        envvar="START_BLOCK",
    )(options)

    options = click.option(
        "-e",
        "--end-block",
        show_default=True,
        type=int,
        help="End block",
        envvar="END_BLOCK",
    )(options)
    return options


def index_record(options):
    options = click.option(
        "--sync-recorder",
        default="file:sync_record",
        show_default=True,
        type=str,
        envvar="SYNC_RECORDER",
        help="How to store the sync record data."
        'e.g pg:base. means sync record data will store in pg as "base" be key'
        'or file:base. means sync record data will store in file as "base" be file name',
    )(options)

    options = click.option(
        "--retry-from-record",
        show_default=True,
        type=bool,
        envvar="RETRY_FROM_RECORD",
        help="With the default parameter, the program will always run from the -s parameter, "
        "and when set to True, it will run from the record point between -s and -e",
    )(options)

    return options
