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
    "SyncRecord": "exporters.jdbc.schema.sync_record",
    "Blocks": "exporters.jdbc.schema.blocks",
    "Transactions": "exporters.jdbc.schema.transactions",
    "Logs": "exporters.jdbc.schema.logs",
    "Traces": "exporters.jdbc.schema.traces",
    "ContractInternalTransactions": "exporters.jdbc.schema.contract_internal_transactions",
    "Contracts": "exporters.jdbc.schema.contracts",
    "CoinBalances": "exporters.jdbc.schema.coin_balances",
    "ERC20TokenTransfers": "exporters.jdbc.schema.erc20_token_transfers",
    "ERC20TokenHolders": "exporters.jdbc.schema.erc20_token_holders",
    "ERC721TokenTransfers": "exporters.jdbc.schema.erc721_token_transfers",
    "ERC721TokenHolders": "exporters.jdbc.schema.erc721_token_holders",
    "ERC721TokenIdChanges": "exporters.jdbc.schema.erc721_token_id_changes",
    "ERC721TokenIdDetails": "exporters.jdbc.schema.erc721_token_id_details",
    "ERC1155TokenTransfers": "exporters.jdbc.schema.erc1155_token_transfers",
    "ERC1155TokenHolders": "exporters.jdbc.schema.erc1155_token_holders",
    "ERC1155TokenIdDetails": "exporters.jdbc.schema.erc1155_token_id_details",
    "Tokens": "exporters.jdbc.schema.tokens",
    "AddressTokenBalances": "exporters.jdbc.schema.token_balances",
    "BlockTimestampMapper": "exporters.jdbc.schema.block_timestamp_mapper",
}
