import json
import re
from datetime import datetime

from flask import current_app
from web3 import Web3

from hemera.api.app.contract.contract_verify import get_abis_for_logs, get_names_from_method_or_topic_list
from hemera.api.app.db_service.contracts import get_contracts_by_addresses
from hemera.api.app.db_service.tokens import get_token_by_address
from hemera.api.app.utils.fill_info import fill_address_display_to_logs, fill_address_display_to_transactions
from hemera.api.app.utils.format_utils import format_transaction
from hemera.api.app.utils.token_utils import get_token_price
from hemera.common.models.transactions import Transactions
from hemera.common.utils.abi_code_utils import decode_log_data
from hemera.common.utils.config import get_config
from hemera.common.utils.format_utils import bytes_to_hex_str, format_to_dict, row_to_dict
from hemera.common.utils.web3_utils import chain_id_name_mapping

app_config = get_config()

SUPPORT_BRIDGES = {
    "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1": {
        "bridge_name": "Optimism Bridge",
        "bridge_logo": "https://storage.googleapis.com/socialscan-public-asset/bridge/optimism.png",
    },
    "0x3154cf16ccdb4c6d922629664174b904d80f2c35": {
        "bridge_name": "Base Bridge",
        "bridge_logo": "https://www.base.org/_next/static/media/logoBlack.4dc25558.svg",
    },
    "0x72ce9c846789fdb6fc1f34ac4ad25dd9ef7031ef": {
        "bridge_name": "Arbitrum One: L1 Gateway Router",
        "bridge_logo": "https://cryptologos.cc/logos/arbitrum-arb-logo.svg?v=035",
    },
    "0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f": {
        "bridge_name": "Arbitrum: Delayed Inbox",
        "bridge_logo": "https://cryptologos.cc/logos/arbitrum-arb-logo.svg?v=035",
    },
    "0x051f1d88f0af5763fb888ec4378b4d8b29ea3319": {
        "bridge_name": "Linea: ERC20 Bridge",
        "bridge_logo": "https://images.seeklogo.com/logo-png/52/1/linea-logo-png_seeklogo-527155.png",
    },
    "0x504a330327a089d8364c4ab3811ee26976d388ce": {
        "bridge_name": "Linea: USDC Bridge",
        "bridge_logo": "https://images.seeklogo.com/logo-png/52/1/linea-logo-png_seeklogo-527155.png",
    },
    "0xd19d4b5d358258f05d7b411e21a1460d11b0876f": {
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


def parse_transactions(transactions: list[Transactions]):
    transaction_list = []
    if len(transactions) <= 0:
        return transaction_list

    GAS_FEE_TOKEN_PRICE = get_token_price(app_config.token_configuration.gas_fee_token, transactions[0].block_timestamp)

    to_address_list = []
    bytea_address_list = []
    for transaction in transactions:
        to_address_list.append(transaction.to_address)
        bytea_address_list.append(transaction.from_address)
        bytea_address_list.append(transaction.to_address)

        transaction_json = format_to_dict(transaction)
        transaction_json["method_id"] = "0x" + transaction_json["method_id"]
        transaction_json["method"] = transaction_json["method_id"]
        transaction_json["is_contract"] = False
        transaction_json["contract_name"] = None

        if not transaction_json["to_address"]:
            transaction_json["to_address"] = transaction_json["receipt_contract_address"]

        transaction_list.append(format_transaction(float(GAS_FEE_TOKEN_PRICE), transaction_json))

    # Doing this early so we don't need to query contracts twice
    fill_address_display_to_transactions(transaction_list, bytea_address_list)

    # Find contract
    contracts = get_contracts_by_addresses(address_list=to_address_list, columns=["address"])
    contract_list = set(map(lambda x: bytes_to_hex_str(x.address), contracts))

    method_list = []
    for transaction_json in transaction_list:
        if transaction_json["receipt_contract_address"] is not None:
            transaction_json["method"] = "Contract Creation"
        elif transaction_json["method"] == "0x64617461":
            decode_input = Web3.to_text(hexstr=transaction_json["input"])
            if "data:," in decode_input:
                try:
                    inscription = json.loads(decode_input.split("data:,")[1])
                    if inscription:
                        transaction_json["method"] = "Inscription: " + inscription["op"]
                except:
                    pass
        elif transaction_json["to_address"] in contract_list:
            transaction_json["is_contract"] = True
            method_list.append(transaction_json["method"])
        else:
            transaction_json["method"] = "Transfer"

    # match function and function name
    contract_function_abis = get_names_from_method_or_topic_list(method_list)

    for transaction_json in transaction_list:
        for function_abi in contract_function_abis:
            if transaction_json["method"] == function_abi.get("signed_prefix"):
                transaction_json["method"] = " ".join(
                    re.sub(
                        "([A-Z][a-z]+)",
                        r" \1",
                        re.sub("([A-Z]+)", r" \1", function_abi.get("function_name")),
                    ).split()
                ).title()

    return transaction_list


def parse_log_with_transaction_input_list(log_with_transaction_input_list):
    log_list = []
    contract_topic_list = []
    transaction_method_list = []
    count_non_none = lambda x: 0 if x is None else 1
    for log in log_with_transaction_input_list:

        # values as dict format
        log_json = format_to_dict(log.Logs)  # log_with_transaction_input[0]
        indexed_true_count = sum(
            count_non_none(topic) for topic in [log_json["topic1"], log_json["topic2"], log_json["topic3"]]
        )
        contract_topic_list.append((log_json["address"], log_json["topic0"], indexed_true_count))
        log_input = bytes_to_hex_str(log.input)

        if log_input and len(log_input) >= 10:
            transaction_method = log_input[0:10]
            transaction_method_list.append(transaction_method)
            log_json["transaction_method_id"] = transaction_method
        log_list.append(log_json)

    # Get method list by transaction_method_list
    method_list = get_names_from_method_or_topic_list(transaction_method_list)
    method_map = {method.get("signed_prefix"): method for method in method_list}

    address_sign_contract_abi_dict = get_abis_for_logs(contract_topic_list)
    for log_json in log_list:
        # Continue loop if 'topic0' is missing or has a falsy/empty value
        if not log_json.get("topic0"):
            continue
        # Set method id
        topic0_value = log_json["topic0"]
        log_json["method_id"] = topic0_value[0:10]

        # Set function method
        if "transaction_method_id" in log_json and log_json["transaction_method_id"] in method_map:
            log_json["transaction_method"] = method_map[log_json["transaction_method_id"]].get("function_name")
            log_json["transaction_function_unsigned"] = method_map[log_json["transaction_method_id"]].get(
                "function_unsigned"
            )

        event_abi = address_sign_contract_abi_dict.get((log_json["address"], topic0_value))
        if not event_abi:
            continue
        try:
            event_abi_json = json.loads(event_abi.get("function_abi"))
            # Get full data types
            index_data_types = []
            data_types = []

            # Get full data string
            index_data_str = ""
            data_str = log_json["data"][2:]

            for param in event_abi_json["inputs"]:
                if param["indexed"]:
                    index_data_types.append(param["type"])
                    index_data_str += log_json[f"topic{len(index_data_types)}"][2:]
                else:
                    data_types.append(param["type"])
            decoded_index_data, endcoded_index_data = decode_log_data(index_data_types, index_data_str)
            decoded_data, endcoded_data = decode_log_data(data_types, data_str)

            index_input_data = []
            input_data = []
            full_function_name = ""
            for index in range(len(event_abi_json["inputs"])):
                param = event_abi_json["inputs"][index]
                if param["indexed"]:
                    index_input_data.append(
                        {
                            "indexed": param["indexed"],
                            "name": param["name"],
                            "data_type": param["type"],
                            "hex_data": decoded_index_data[len(index_input_data)],
                            "dec_data": endcoded_index_data[len(index_input_data)],
                        }
                    )
                else:
                    input_data.append(
                        {
                            "indexed": param["indexed"],
                            "name": param["name"],
                            "data_type": param["type"],
                            "hex_data": decoded_data[len(input_data)],
                            "dec_data": endcoded_data[len(input_data)],
                        }
                    )
                if param["indexed"]:
                    full_function_name += f"index_topic_{index + 1} {param['type']} {param['name']}, "
                else:
                    full_function_name += f"{param['type']} {param['name']}, "
            function_name = event_abi.get("function_name")
            full_function_name = f"{function_name}({full_function_name[:-2]})"
            log_json["input_data"] = index_input_data + input_data
            log_json["function_name"] = function_name
            log_json["function_unsigned"] = event_abi.get("function_unsigned")
            log_json["full_function_name"] = full_function_name
        except Exception as e:
            current_app.logger.info(e)

    fill_address_display_to_logs(log_list)
    return log_list


def day_parse_int_to_str(day):
    day = str(day)
    date_obj = datetime.strptime(day, "%Y%m%d")
    formatted_date = date_obj.strftime("%Y-%m-%d")
    return formatted_date


def day_parse_str_to_int(day):
    date_obj = datetime.strptime(day, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%Y%m%d")
    return formatted_date
