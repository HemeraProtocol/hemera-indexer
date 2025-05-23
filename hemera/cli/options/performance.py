import click


def delay_control(options):
    options = click.option(
        "--period-seconds",
        show_default=True,
        type=float,
        envvar="PERIOD_SECONDS",
        help="How many seconds to sleep between syncs",
    )(options)

    options = click.option(
        "--delay",
        show_default=True,
        type=int,
        envvar="DELAY",
        help="The limit number of blocks which delays from the network current block number.",
    )(options)

    return options


def block_step(options):
    options = click.option(
        "-B",
        "--block-batch-size",
        show_default=True,
        type=int,
        envvar="BLOCK_BATCH_SIZE",
        help="How many blocks to batch in single sync round",
    )(options)

    return options


def single_performance(options):
    options = click.option(
        "-b",
        "--batch-size",
        show_default=True,
        type=int,
        envvar="BATCH_SIZE",
        help="The number of non-debug RPC requests to batch in a single request",
    )(options)

    options = click.option(
        "--debug-batch-size",
        show_default=True,
        type=int,
        envvar="DEBUG_BATCH_SIZE",
        help="The number of debug RPC requests to batch in a single request",
    )(options)

    options = click.option(
        "-w",
        "--max-workers",
        default=5,
        show_default=True,
        type=int,
        help="The number of workers during a request to rpc.",
        envvar="MAX_WORKERS",
    )(options)

    options = click.option(
        "-m",
        "--multicall",
        show_default=True,
        type=bool,
        help="if `multicall` is set to True, it will decrease the consume of rpc calls",
        envvar="MULTI_CALL_ENABLE",
    )(options)

    return options


def multi_performance(options):
    options = click.option(
        "-pn",
        "--process-numbers",
        show_default=True,
        type=int,
        help="The processor numbers to ues.",
        envvar="PROCESS_NUMBERS",
    )(options)

    options = click.option(
        "-ps",
        "--process-size",
        show_default=True,
        type=int,
        help="The data size for every process to handle. Default to {B}/{pn} ,see above",
        envvar="PROCESS_SIZE",
    )(options)

    options = click.option(
        "-pto",
        "--process-time-out",
        show_default=True,
        type=int,
        help="Timeout for every processor, default to {ps} * 300 , see above",
        envvar="PROCESS_TIME_OUT",
    )(options)

    return options
