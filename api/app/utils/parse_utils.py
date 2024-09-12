
from api.app.db_service.tokens import get_token_by_address
from common.utils.format_utils import row_to_dict
from common.utils.web3_utils import chain_id_name_mapping



def parse_deposit_assets(assets):
    asset_list = []
    for asset in assets:
        asset_dict = row_to_dict(asset)

        token_info = get_token_by_address(
            asset_dict["token_address"], ["name", "symbol", "decimals", "icon_url", "token_type"]
        )
        decimals = int(token_info.decimals) if token_info else 18
        asset_list.append(
            {
                "chain": chain_id_name_mapping[asset_dict["chain_id"]],
                "bridge": asset_dict["contract_address"],
                "token": asset_dict["token_address"],
                "token_name": token_info.name if token_info else None,
                "token_symbol": token_info.symbol if token_info else None,
                "token_icon_url": token_info.icon_url if token_info else None,
                "token_type": token_info.token_type if token_info else None,
                "amount": "{0:.18f}".format(asset_dict["value"] / 10 ** decimals).rstrip("0").rstrip("."),
            }
        )

    return asset_list


def parse_deposit_transactions(transactions):
    transaction_list = []
    for transaction in transactions:
        tx_dict = row_to_dict(transaction)
        tx_dict["chain_name"] = chain_id_name_mapping[tx_dict["chain_id"]]

        token_info = get_token_by_address(
            tx_dict["token_address"], ["name", "symbol", "decimals", "icon_url", "token_type"]
        )
        decimals = int(token_info.decimals) if token_info else 18
        tx_dict["token_name"] = token_info.name if token_info else None
        tx_dict["token_symbol"] = token_info.symbol if token_info else None
        tx_dict["token_icon_url"] = token_info.icon_url if token_info else None
        tx_dict["token_type"] = token_info.token_type if token_info else None

        tx_dict["value"] = "{0:.18f}".format(tx_dict["value"] / 10**decimals).rstrip("0").rstrip(".")

        transaction_list.append(tx_dict)
    return transaction_list
