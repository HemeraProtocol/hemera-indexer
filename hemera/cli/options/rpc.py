import click


def rpc_provider(options):
    options = click.option(
        "-p",
        "--provider-uri",
        default="https://ethereum-rpc.publicnode.com",
        show_default=True,
        type=str,
        envvar="PROVIDER_URI",
        help="The URI of the web3 provider e.g. "
        "file://$HOME/Library/Ethereum/geth.ipc or https://ethereum-rpc.publicnode.com",
    )(options)

    options = click.option(
        "-d",
        "--debug-provider-uri",
        default="https://ethereum-rpc.publicnode.com",
        show_default=True,
        type=str,
        envvar="DEBUG_PROVIDER_URI",
        help="The URI of the web3 debug provider e.g. "
        "file://$HOME/Library/Ethereum/geth.ipc or https://ethereum-rpc.publicnode.com",
    )(options)

    return options
