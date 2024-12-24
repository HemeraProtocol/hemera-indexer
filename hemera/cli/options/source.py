import click


def source_control(options):
    options = click.option(
        "--source-path",
        show_default=True,
        required=False,
        type=str,
        envvar="SOURCE_PATH",
        help="The path to load the data."
        "Load from postgres e.g. postgresql://postgres:admin@127.0.0.1:5432/ethereum"
        "or local csv file e.g. csvfile://your-file-direction; "
        "or local json file e.g. jsonfile://your-file-direction; ",
    )(options)

    options = click.option(
        "--source-types",
        default="block,transaction,log",
        show_default=True,
        type=str,
        envvar="SOURCE_TYPES",
        help="The list of types to read from source, corresponding to more detailed data models. "
        "Examples include: block, transaction, log, "
        "token, address_token_balance, erc20_token_transfer, erc721_token_transfer, erc1155_token_transfer, "
        "trace, contract, coin_balance.",
    )(options)

    return options
