from sqlalchemy.orm import declarative_base
from utils.module_loading import import_string

Base = declarative_base()


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
    "Blocks": "exporters.jdbc.schema.blocks",
    "Transactions": "exporters.jdbc.schema.transactions",
    "Logs": "exporters.jdbc.schema.logs",
    "Traces": "exporters.jdbc.schema.traces",
    "ContractInternalTransactions": "exporters.jdbc.schema.contract_internal_transactions",
    "Contracts": "exporters.jdbc.schema.contracts",
    "CoinBalances": "exporters.jdbc.schema.coin_balances",
    "TokenTransfers": "exporters.jdbc.schema.token_transfers",
    "TokenBalances": "exporters.jdbc.schema.token_balances",
    "BlockTimestampMapper": "exporters.jdbc.schema.block_timestamp_mapper",
}
