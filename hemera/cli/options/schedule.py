import click

from hemera.common.enumeration.entity_type import DEFAULT_COLLECTION


def job_schedule(options):
    options = click.option(
        "-E",
        "--entity-types",
        default=",".join(DEFAULT_COLLECTION),
        show_default=True,
        type=str,
        envvar="ENTITY_TYPES",
        help="The list of entity types to export. " "e.g. EXPLORER_BASE | EXPLORER_TOKEN | EXPLORER_TRACE",
    )(options)

    options = click.option(
        "-O",
        "--output-types",
        show_default=True,
        type=str,
        envvar="OUTPUT_TYPES",
        help="The list of output types to export, corresponding to more detailed data models. "
        "Specifying this option will prioritize these settings over the entity types specified in -E. "
        "Examples include: block, transaction, log, "
        "token, address_token_balance, erc20_token_transfer, erc721_token_transfer, erc1155_token_transfer, "
        "trace, contract, coin_balance.",
    )(options)

    return options


def job_config(options):
    options = click.option(
        "--config-file",
        show_default=True,
        type=str,
        envvar="CONFIG_FILE",
        help="The path to the configuration file, if provided, the configuration file will be used to load the configuration. Supported formats are json and yaml.",
    )(options)

    return options


def filter_mode(options):
    options = click.option(
        "--force-filter-mode",
        default=False,
        show_default=True,
        type=bool,
        envvar="FORCE_FILTER_MODE",
        help="Force the filter mode to be enabled, even if no filters job are provided.",
    )(options)

    return options


def reorg_switch(options):
    options = click.option(
        "--auto-reorg",
        default=False,
        show_default=True,
        type=bool,
        envvar="AUTO_REORG",
        help="Whether to detect reorg in data streams and automatically repair data.",
    )(options)

    return options
