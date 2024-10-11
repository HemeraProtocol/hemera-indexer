from api.app.db_service.contracts import get_contracts_by_addresses
from api.app.db_service.wallet_addresses import get_address_display_mapping
from common.utils.format_utils import format_to_dict, hex_str_to_bytes


def fill_address_display_to_logs(log_list, all_address_list=None):
    if not all_address_list:
        all_address_list = []
    for log in log_list:
        all_address_list.append(hex_str_to_bytes(log["address"]))

    address_map = get_address_display_mapping(all_address_list)
    for log in log_list:
        if log["address"] in address_map:
            log["address_display_name"] = address_map[log["address"]]


def fill_is_contract_to_transactions(transaction_list: list[dict], bytea_address_list: list[bytes] = None):
    if not bytea_address_list:
        bytea_address_list = []
        for transaction in transaction_list:
            bytea_address_list.append(hex_str_to_bytes(transaction["from_address"]))
            bytea_address_list.append(hex_str_to_bytes(transaction["to_address"]))

    contracts = get_contracts_by_addresses(address_list=bytea_address_list, columns=["address"])
    contract_list = set(map(lambda x: x.address, contracts))

    for transaction_json in transaction_list:
        if transaction_json["to_address"] in contract_list:
            transaction_json["to_address_is_contract"] = True
        if transaction_json["from_address"] in contract_list:
            transaction_json["from_address_is_contract"] = True


def fill_address_display_to_transactions(transaction_list: list[dict], bytea_address_list: list[bytes] = None):
    if not bytea_address_list:
        bytea_address_list = []
        for transaction in transaction_list:
            bytea_address_list.append(hex_str_to_bytes(transaction["from_address"]))
            bytea_address_list.append(hex_str_to_bytes(transaction["to_address"]))

    address_map = get_address_display_mapping(bytea_address_list)

    for transaction_json in transaction_list:
        if transaction_json["from_address"] in address_map:
            transaction_json["from_address_display_name"] = address_map[transaction_json["from_address"]]
        else:
            transaction_json["from_address_display_name"] = transaction_json["from_address"]

        if transaction_json["to_address"] in address_map:
            transaction_json["to_address_display_name"] = address_map[transaction_json["to_address"]]
        else:
            transaction_json["to_address_display_name"] = transaction_json["to_address"]


def process_token_transfer(token_transfers, token_type):
    token_transfer_list = []
    for token_transfer in token_transfers:
        token_transfer_json = format_to_dict(token_transfer)
        token_transfer_json["type"] = token_type
        token_transfer_json["token_symbol"] = token_transfer.symbol or "UNKNOWN"
        token_transfer_json["token_name"] = token_transfer.name or "Unknown Token"

        if token_type == "tokentxns":
            token_transfer_json["value"] = (
                "{0:.18f}".format(token_transfer.value / 10 ** (token_transfer.decimals or 18)).rstrip("0").rstrip(".")
            )
            token_transfer_json["token_logo_url"] = token_transfer.icon_url or None
        else:
            token_transfer_json["token_id"] = "{:f}".format(token_transfer.token_id)
            token_transfer_json["token_logo_url"] = None
            if token_type == "tokentxns-nft1155":
                token_transfer_json["value"] = "{:f}".format(token_transfer.value)

        token_transfer_list.append(token_transfer_json)
    return token_transfer_list
