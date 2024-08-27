#!/usr/bin/python3
# -*- coding: utf-8 -*-
import copy
import json
import re
from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy import text
from sqlalchemy.sql import text
from web3 import Web3

from api.app.contract.contract_verify import get_abis_for_logs, get_names_from_method_or_topic_list
from api.app.db_service.contracts import get_contracts_by_addresses
from api.app.db_service.wallet_addresses import get_address_display_mapping
from api.app.token.token_prices import get_token_price
from common.models import db
from common.models.transactions import Transactions
from common.utils.config import get_config
from common.utils.format_utils import format_coin_value, format_to_dict, row_to_dict
from common.utils.web3_utils import decode_log_data

app_config = get_config()


def get_count_by_address(table, chain, wallet_address=None):
    if not wallet_address:
        return get_total_row_count(table)

    # Try to get count from redis
    # get_count(f"{chain}_{table}_{wallet_address}")


def get_total_row_count(table):

    estimate_transaction = db.session.execute(
        text(
            f"""
            SELECT reltuples::bigint AS estimate FROM pg_class where oid = '{app_config.db_read_sql_alchemy_database_config.schema}.{table}'::regclass;
        """
        )
    ).fetchone()
    return estimate_transaction[0]


def fill_address_display_to_logs(log_list, all_address_list=None):
    if not all_address_list:
        all_address_list = []
    for log in log_list:
        all_address_list.append(bytes.fromhex(log["address"][2:]))

    address_map = get_address_display_mapping(all_address_list)
    for log in log_list:
        if log["address"] in address_map:
            log["address_display_name"] = address_map[log["address"]]


def fill_is_contract_to_transactions(transaction_list: list[dict], bytea_address_list: list[bytes] = None):
    if not bytea_address_list:
        bytea_address_list = []
        for transaction in transaction_list:
            bytea_address_list.append(bytes.fromhex(transaction["from_address"][2:]))
            bytea_address_list.append(bytes.fromhex(transaction["to_address"][2:]))

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
            bytea_address_list.append(bytes.fromhex(transaction["from_address"][2:]))
            bytea_address_list.append(bytes.fromhex(transaction["to_address"][2:]))

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


def format_transaction(GAS_FEE_TOKEN_PRICE, transaction: dict):
    transaction_json = copy.copy(transaction)
    transaction_json["gas_fee_token_price"] = "{0:.2f}".format(GAS_FEE_TOKEN_PRICE)

    transaction_json["value"] = format_coin_value(int(transaction["value"]))
    transaction_json["value_dollar"] = "{0:.2f}".format(transaction["value"] * GAS_FEE_TOKEN_PRICE / 10**18)

    transaction_json["gas_price_gwei"] = "{0:.6f}".format(transaction["gas_price"] / 10**9).rstrip("0").rstrip(".")
    transaction_json["gas_price"] = "{0:.15f}".format(transaction["gas_price"] / 10**18).rstrip("0").rstrip(".")

    transaction_fee = transaction["gas_price"] * transaction["receipt_gas_used"]
    total_transaction_fee = transaction["gas_price"] * transaction["receipt_gas_used"]

    if "receipt_l1_fee" in transaction_json and transaction_json["receipt_l1_fee"]:
        transaction_json["receipt_l1_fee"] = (
            "{0:.15f}".format(transaction["receipt_l1_fee"] / 10**18).rstrip("0").rstrip(".")
        )
        transaction_json["receipt_l1_gas_price"] = (
            "{0:.15f}".format(transaction["receipt_l1_gas_price"] / 10**18).rstrip("0").rstrip(".")
        )
        transaction_json["receipt_l1_gas_price_gwei"] = (
            "{0:.6f}".format(transaction["receipt_l1_gas_price"] / 10**9).rstrip("0").rstrip(".")
        )

        total_transaction_fee = transaction_fee + transaction["receipt_l1_fee"]
    transaction_json["transaction_fee"] = "{0:.15f}".format(transaction_fee / 10**18).rstrip("0").rstrip(".")
    transaction_json["transaction_fee_dollar"] = "{0:.2f}".format(
        transaction["gas_price"] * GAS_FEE_TOKEN_PRICE * transaction["receipt_gas_used"] / 10**18
    )

    transaction_json["total_transaction_fee"] = (
        "{0:.15f}".format(total_transaction_fee / 10**18).rstrip("0").rstrip(".")
    )
    transaction_json["total_transaction_fee_dollar"] = "{0:.2f}".format(
        total_transaction_fee * GAS_FEE_TOKEN_PRICE / 10**18
    )
    return transaction_json


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
    contract_list = set(map(lambda x: x.address, contracts))

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


def solve_nested_components(json_object, sb):
    string = json_object.get("type")

    if json_object.get("components"):
        components = json_object.get("components")
        sb.append("(")

        for j in range(len(components)):
            json_object1 = components[j]
            if json_object1.get("components"):
                solve_nested_components(json_object1, sb)
            else:
                inner_type = json_object1.get("type")
                sb.append(inner_type)

            if j < len(components) - 1:
                sb.append(",")

        sb.append(")")
        while string.endswith("[]"):
            sb.append("[]")
            string = string[:-2]
    else:
        sb.append(string)


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
        log_input = "0x" + log.input.hex()

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


def is_l1_block_finalized(block_number, timestamp):
    return timestamp < datetime.utcnow() - timedelta(minutes=15)


def is_l2_challenge_period_pass(block_number, timestamp):
    return timestamp < datetime.utcnow() - timedelta(days=7) - timedelta(minutes=15)


def day_parse_int_to_str(day):
    day = str(day)
    date_obj = datetime.strptime(day, "%Y%m%d")
    formatted_date = date_obj.strftime("%Y-%m-%d")
    return formatted_date


def day_parse_str_to_int(day):
    date_obj = datetime.strptime(day, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%Y%m%d")
    return formatted_date


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
