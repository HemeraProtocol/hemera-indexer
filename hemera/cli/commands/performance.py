import click


def delay_control(commands):
    commands = click.option(
        "--period-seconds",
        default=None,
        show_default=True,
        type=float,
        envvar="PERIOD_SECONDS",
        help="How many seconds to sleep between syncs",
    )(commands)

    commands = click.option(
        "--delay",
        default=None,
        show_default=True,
        type=int,
        envvar="DELAY",
        help="The limit number of blocks which delays from the network current block number.",
    )(commands)

    return commands


def block_step(commands):
    commands = click.option(
        "-B",
        "--block-batch-size",
        default=None,
        show_default=True,
        type=int,
        envvar="BLOCK_BATCH_SIZE",
        help="How many blocks to batch in single sync round",
    )(commands)

    return commands


def single_performance(commands):
    commands = click.option(
        "-b",
        "--batch-size",
        default=None,
        show_default=True,
        type=int,
        envvar="BATCH_SIZE",
        help="The number of non-debug RPC requests to batch in a single request",
    )(commands)

    commands = click.option(
        "--debug-batch-size",
        default=None,
        show_default=True,
        type=int,
        envvar="DEBUG_BATCH_SIZE",
        help="The number of debug RPC requests to batch in a single request",
    )(commands)

    commands = click.option(
        "-w",
        "--max-workers",
        default=5,
        show_default=True,
        type=int,
        help="The number of workers during a request to rpc.",
        envvar="MAX_WORKERS",
    )(commands)

    commands = click.option(
        "-m",
        "--multicall",
        default=None,
        show_default=True,
        type=bool,
        help="if `multicall` is set to True, it will decrease the consume of rpc calls",
        envvar="MULTI_CALL_ENABLE",
    )(commands)

    return commands


def multi_performance(commands):
    commands = click.option(
        "-pn",
        "--process-numbers",
        default=None,
        show_default=True,
        type=int,
        help="The processor numbers to ues.",
        envvar="PROCESS_NUMBERS",
    )(commands)

    commands = click.option(
        "-ps",
        "--process-size",
        default=None,
        show_default=True,
        type=int,
        help="The data size for every process to handle. Default to {B}/{pn} ,see above",
        envvar="PROCESS_SIZE",
    )(commands)

    commands = click.option(
        "-pto",
        "--process-time-out",
        default=None,
        show_default=True,
        type=int,
        help="Timeout for every processor, default to {ps} * 300 , see above",
        envvar="PROCESS_TIME_OUT",
    )(commands)

    return commands
