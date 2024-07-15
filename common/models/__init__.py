from alembic import context
from flask import Flask

from common.services.sqlalchemy_session import RouteSQLAlchemy
from common.utils.module_loading import import_string

db = RouteSQLAlchemy(session_options={"autoflush": False})


def init_app():
    app = Flask(__name__)
    config = context.config
    app.config['SQLALCHEMY_DATABASE_URI'] = config.get_main_option("sqlalchemy.url")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    return app


def import_all_models():
    for name in __lazy_imports:
        __getattr__(name)


def __getattr__(name):
    if name != "ImportError":
        path = __lazy_imports.get(name)
        if not path:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

        val = import_string(f"{path}.{name}")

    # Store for next time
    globals()[name] = val
    return val


__lazy_imports = {
    "SyncRecord": "common.models.sync_record",
    "FixRecord": "common.models.fix_record",
    "Blocks": "common.models.blocks",
    "Transactions": "common.models.transactions",
    "Logs": "common.models.logs",
    "Traces": "common.models.traces",
    "ContractInternalTransactions": "common.models.contract_internal_transactions",
    "Contracts": "common.models.contracts",
    "CoinBalances": "common.models.coin_balances",
    "ERC20TokenTransfers": "common.models.erc20_token_transfers",
    "ERC20TokenHolders": "common.models.erc20_token_holders",
    "ERC721TokenTransfers": "common.models.erc721_token_transfers",
    "ERC721TokenHolders": "common.models.erc721_token_holders",
    "ERC721TokenIdChanges": "common.models.erc721_token_id_changes",
    "ERC721TokenIdDetails": "common.models.erc721_token_id_details",
    "ERC1155TokenTransfers": "common.models.erc1155_token_transfers",
    "ERC1155TokenHolders": "common.models.erc1155_token_holders",
    "ERC1155TokenIdDetails": "common.models.erc1155_token_id_details",
    "Tokens": "common.models.tokens",
    "AddressTokenBalances": "common.models.token_balances",
    "BlockTimestampMapper": "common.models.block_timestamp_mapper",
}
