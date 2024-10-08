from api.app.db_service.tokens import get_token_by_address
from common.utils.format_utils import row_to_dict
from common.utils.web3_utils import chain_id_name_mapping

SUPPORT_BRIDGES = {
    "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1": {
        "bridge_name": "Optimism Bridge",
        "bridge_logo": "https://storage.googleapis.com/socialscan-public-asset/bridge/optimism.png",
    },
    "0x3154Cf16ccdb4C6d922629664174b904d80F2C35": {
        "bridge_name": "Base Bridge",
        "bridge_logo": "https://www.base.org/_next/static/media/logoBlack.4dc25558.svg",
    },
    "0x72Ce9c846789fdB6fC1f34aC4AD25Dd9ef7031ef": {
        "bridge_name": "Arbitrum One: L1 Gateway Router",
        "bridge_logo": "https://cryptologos.cc/logos/arbitrum-arb-logo.svg?v=035",
    },
    "0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f": {
        "bridge_name": "Arbitrum: Delayed Inbox",
        "bridge_logo": "https://cryptologos.cc/logos/arbitrum-arb-logo.svg?v=035",
    },
    "0x051F1D88f0aF5763fB888eC4378b4D8B29ea3319": {
        "bridge_name": "Linea: ERC20 Bridge",
        "bridge_logo": "https://images.seeklogo.com/logo-png/52/1/linea-logo-png_seeklogo-527155.png",
    },
    "0x504A330327A089d8364C4ab3811Ee26976d388ce": {
        "bridge_name": "Linea: USDC Bridge",
        "bridge_logo": "https://images.seeklogo.com/logo-png/52/1/linea-logo-png_seeklogo-527155.png",
    },
    "0xd19d4B5d358258f05D7B411E21A1460D11B0876F": {
        "bridge_name": "Linea: L1 Message Service",
        "bridge_logo": "https://images.seeklogo.com/logo-png/52/1/linea-logo-png_seeklogo-527155.png",
    },
}


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
                "bridge_contract_address": asset_dict["contract_address"],
                "bridge_name": SUPPORT_BRIDGES[asset_dict["contract_address"]]["bridge_name"],
                "bridge_logo": SUPPORT_BRIDGES[asset_dict["contract_address"]]["bridge_logo"],
                "token": asset_dict["token_address"],
                "token_name": token_info.name if token_info else None,
                "token_symbol": token_info.symbol if token_info else None,
                "token_icon_url": token_info.icon_url if token_info else None,
                "token_type": token_info.token_type if token_info else None,
                "amount": "{0:.18f}".format(asset_dict["value"] / 10**decimals).rstrip("0").rstrip("."),
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
