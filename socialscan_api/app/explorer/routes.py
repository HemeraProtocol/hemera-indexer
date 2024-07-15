#!/usr/bin/python3
# -*- coding: utf-8 -*-
import csv
import io
import json
import logging
import string
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import flask
import sqlalchemy
from flask import Response
from flask_restx import Resource, reqparse
from sqlalchemy import nullslast, cast
from sqlalchemy.sql import and_, func, or_
from sqlalchemy.dialects.postgresql import VARCHAR

from common.models import db
from common.models.blocks import Blocks
from common.models.contract_internal_transactions import ContractInternalTransactions
from common.models.contracts import Contracts
from common.models.daily_address_aggreggates import DailyAddressesAggregates
from common.models.daily_blocks_aggreggates import DailyBlocksAggregates
from common.models.daily_tokens_aggreggates import DailyTokensAggregates
from common.models.daily_transactions_aggreggates import DailyTransactionsAggregates
from common.models.erc1155_token_holders import ERC1155TokenHolders
from common.models.erc1155_token_transfers import ERC1155TokenTransfers
from common.models.erc20_token_holders import ERC20TokenHolders
from common.models.erc20_token_transfers import ERC20TokenTransfers
from common.models.erc721_token_holders import ERC721TokenHolders
from common.models.erc721_token_transfers import ERC721TokenTransfers
from common.models.logs import Logs
from common.models.tokens import Tokens
from common.models.traces import Traces
from common.models.transactions import Transactions
from common.models.wallet_addresses import WalletAddresses
from common.models.wallet_addresses import WalletAddresses as StatisticsWalletAddresses
from common.utils.config import get_config
from common.utils.format_utils import as_dict, format_coin_value_with_unit, row_to_dict
from socialscan_api.app.cache import cache
from socialscan_api.app.contract.contract_verify import get_abis_for_method, get_sha256_hash, get_similar_addresses
from socialscan_api.app.db_service.blocks import get_last_block, get_block_by_number
from socialscan_api.app.db_service.tokens import get_address_token_transfer_cnt, get_token_address_token_transfer_cnt, \
    type_to_token_transfer_table, get_raw_token_transfers, parse_token_transfers
from socialscan_api.app.db_service.transactions import get_last_transaction, get_address_transaction_cnt, \
    get_total_txn_count, get_tps_latest_10min
from socialscan_api.app.explorer import explorer_namespace
from common.models.token_balances import AddressTokenBalances

from socialscan_api.app.utils.utils import (
    fill_address_display_to_transactions,
    get_total_row_count,
    parse_log_with_transaction_input_list,
    parse_transactions,
    process_token_transfer,
)
from common.utils.web3_utils import (
    decode_function,
    decode_log_data,
    get_balance,
    get_code,
    get_debug_trace_transaction,
    get_gas_price,
    is_eth_address,
    is_eth_transaction_hash,
    to_checksum_address,
)

from common.utils.exception_control import APIError
from socialscan_api.app.db_service.wallet_addresses import get_address_display_mapping, get_ens_mapping
from socialscan_api.app.token.token_prices import get_token_price

PAGE_SIZE = 25
MAX_TRANSACTION = 500000
MAX_TRANSACTION_WITH_CONDITION = 10000
MAX_INTERNAL_TRANSACTION = 10000
MAX_TOKEN_TRANSFER = 10000

app_config = get_config()


@explorer_namespace.route("/v1/explorer/health")
class ExplorerHealthCheck(Resource):
    def get(self):
        return {
            "engine_pool_status": db.engine.pool.status(),
            "status": "OK",
        }, 200


@explorer_namespace.route("/v1/explorer/stats")
class ExplorerMainStats(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self):
        # Slow ~300ms
        transaction_count = get_total_txn_count()

        last_transaction = get_last_transaction()
        transaction_tps = get_tps_latest_10min(last_transaction.block_timestamp)

        lastest_batch_number = 0
        # For zkevm

        # if app_config.l2_config.rollup_type:
        #     lastest_batch_number = get_latest_batch_index()

        lastest_block = get_last_block()
        lastest_block_number = lastest_block.number
        earlier_block_number = max(lastest_block_number - 5000, 1)
        earlier_block = get_block_by_number(earlier_block_number)

        if earlier_block is None:
            earlier_block = lastest_block

        avg_block_time = (lastest_block.timestamp.timestamp() - earlier_block.timestamp.timestamp()) / (
                (lastest_block_number - earlier_block_number) or 1
        )

        BTC_PRICE = get_token_price("WBTC")
        ETH_PRICE = get_token_price("ETH")
        ETH_PRICE_PRIVIOUS = get_token_price(
            "ETH",
            datetime.combine(datetime.now() - timedelta(days=1), time.min),
        )
        TIA_PRICE = get_token_price("TIA")
        TIA_PRICE_PRIVIOUS = get_token_price(
            "TIA",
            datetime.combine(datetime.now() - timedelta(days=1), time.min),
        )
        # MATIC_PRICE = get_matic_price()
        # MATIC_PRICE_PRIVIOUS = get_matic_price(datetime.now() - timedelta(days=1))

        if app_config.token_configuration.native_token == "ETH":
            NATIVE_TOKEN_PRICE = ETH_PRICE
            NATIVE_TOKEN_PRICE_PRIVIOUS = ETH_PRICE_PRIVIOUS
        else:
            NATIVE_TOKEN_PRICE = get_token_price(app_config.token_configuration.native_token)
            NATIVE_TOKEN_PRICE_PRIVIOUS = get_token_price(
                app_config.token_configuration.native_token,
                datetime.combine(datetime.now() - timedelta(days=1), time.min),
            )

        if app_config.token_configuration.dashboard_token == app_config.token_configuration.native_token:
            DASHBOARD_TOKEN_PRICE = NATIVE_TOKEN_PRICE
            DASHBOARD_TOKEN_PRICE_PRIVIOUS = NATIVE_TOKEN_PRICE_PRIVIOUS
        else:
            DASHBOARD_TOKEN_PRICE = get_token_price(app_config.token_configuration.dashboard_token)
            DASHBOARD_TOKEN_PRICE_PRIVIOUS = get_token_price(
                app_config.token_configuration.dashboard_token,
                datetime.combine(datetime.now() - timedelta(days=1), time.min),
            )

        return {
            "total_transactions": transaction_count,
            "transaction_tps": round(transaction_tps, 2),
            "latest_batch": lastest_batch_number,
            "latest_block": lastest_block_number,
            "avg_block_time": avg_block_time,
            "eth_price": "{0:.2f}".format(ETH_PRICE),
            "eth_price_btc": "{0:.5f}".format(ETH_PRICE / (BTC_PRICE or 1)),
            "eth_price_diff": "{0:.4f}".format((ETH_PRICE - ETH_PRICE_PRIVIOUS) / (ETH_PRICE_PRIVIOUS or 1)),
            "tia_price": "{0:.2f}".format(TIA_PRICE),
            "tia_price_eth": "{0:.5f}".format(TIA_PRICE / (ETH_PRICE or 1)),
            "tia_price_diff": "{0:.4f}".format((TIA_PRICE - TIA_PRICE_PRIVIOUS) / (TIA_PRICE_PRIVIOUS or 1)),
            "native_token_price": "{0:.6}".format(NATIVE_TOKEN_PRICE),
            "native_token_price_eth": "{0:.5f}".format(NATIVE_TOKEN_PRICE / (ETH_PRICE or 1)),
            "native_token_price_diff": (
                "{0:.4f}".format(
                    (NATIVE_TOKEN_PRICE - NATIVE_TOKEN_PRICE_PRIVIOUS) / (NATIVE_TOKEN_PRICE_PRIVIOUS or 1)
                )
                if NATIVE_TOKEN_PRICE_PRIVIOUS != 0
                else 0
            ),
            "dashboard_token_price_eth": "{0:.5f}".format(DASHBOARD_TOKEN_PRICE / (ETH_PRICE or 1)),
            "dashboard_token_price": "{0:.6}".format(DASHBOARD_TOKEN_PRICE),
            "dashboard_token_price_diff": (
                "{0:.4f}".format(
                    (DASHBOARD_TOKEN_PRICE - DASHBOARD_TOKEN_PRICE_PRIVIOUS) / (DASHBOARD_TOKEN_PRICE_PRIVIOUS or 1)
                )
                if DASHBOARD_TOKEN_PRICE_PRIVIOUS != 0
                else 0
            ),
            "gas_fee": "{0:1f}".format(get_gas_price() / 10 ** 9).rstrip("0").rstrip(".") + " Gwei",
        }, 200


@explorer_namespace.route("/v1/explorer/charts/transactions_per_day")
class ExplorerChartsTransactionsPerDay(Resource):
    @cache.cached(timeout=300, query_string=True)
    def get(self):
        results = (
            db.session.query(DailyTransactionsAggregates)
            .with_entities(
                func.DATE(DailyTransactionsAggregates.block_date).label("date"),
                DailyTransactionsAggregates.cnt,
            )
            .order_by(
                DailyTransactionsAggregates.block_date.desc(),
            )
            .limit(14)
        )

        date_list = []
        for item in results:
            date_list.append({"value": item.date.isoformat(), "count": item.cnt})

        return {
            "title": "Daily Transactions Chart",
            "data": date_list,
        }, 200


@explorer_namespace.route("/v1/explorer/search")
class ExplorerSearch(Resource):
    @cache.cached(timeout=360, query_string=True)
    def get(self):
        query_string = flask.request.args.get("q")
        if not query_string:
            raise APIError("Missing query string", code=400)
        query_string = query_string.lower()

        search_result = []
        if query_string.isdigit():
            block = Blocks.query.filter(Blocks.number == int(query_string)).first()
            if block is not None:
                search_result.append(
                    {
                        "block_hash": '0x' + block.hash.hex(),
                        "block_number": block.number,
                        "type": "block",
                    }
                )

        # Top priority, search wallet_address
        if is_eth_address(query_string):
            bytes_string = bytes.fromhex(query_string[2:])
            contract = Contracts.query.filter(Contracts.address == bytes_string).first()
            if contract:
                search_result.append(
                    {
                        "wallet_address": '0x' + contract.address.hex(),
                        "type": "address",
                    }
                )
                return search_result
            else:
                wallet = (
                    db.session.query(Transactions)
                    .with_entities(Transactions.from_address.label("address"))
                    .filter(Transactions.from_address == bytes_string)
                    .first()
                )
                if wallet:
                    search_result.append(
                        {
                            "wallet_address": '0x' + wallet.address.hex(),
                            "type": "address",
                        }
                    )
                    return search_result
                else:
                    wallet = (
                        db.session.query(Transactions)
                        .with_entities(Transactions.to_address.label("address"))
                        .filter(Transactions.to_address == bytes_string)
                        .first()
                    )
                    if wallet:
                        search_result.append(
                            {
                                "wallet_address": '0x' + wallet.address.hex(),
                                "type": "address",
                            }
                        )
                        return search_result

        # Check transaction hash
        if is_eth_transaction_hash(query_string):
            bytes_string = bytes.fromhex(query_string[2:])
            transaction = (
                db.session.query(Transactions)
                .with_entities(Transactions.hash)
                .filter(Transactions.hash == bytes_string)
                .first()
            )
            if transaction:
                search_result.append(
                    {
                        "transaction_hash": '0x' + transaction.hash.hex(),
                        "type": "transaction",
                    }
                )
                return search_result
            else:
                block = (
                    db.session.query(Blocks)
                    .with_entities(Blocks.hash, Blocks.number)
                    .filter(Blocks.hash == bytes_string)
                    .first()
                )
                if block:
                    search_result.append(
                        {
                            "block_hash": '0x' + block.hash.hex(),
                            "block_number": block.number,
                            "type": "block",
                        }
                    )
                    return search_result

        # search token
        if len(query_string) > 1:
            erc20_tokens = (
                db.session.query(Tokens)
                .with_entities(
                    Tokens.name,
                    Tokens.symbol,
                    Tokens.address,
                )
                .filter(
                    and_(
                        Tokens.token_type == 'ERC20'
                        ,
                        or_(
                            Tokens.name.ilike(f"%{query_string}%"),
                            Tokens.symbol.ilike(f"%{query_string}%"),
                        )
                    )

                )
                .limit(5)
                .all()
            )
            erc721_tokens = (
                db.session.query(Tokens)
                .with_entities(
                    Tokens.name,
                    Tokens.symbol,
                    Tokens.address,
                )
                .filter(
                    and_(
                        Tokens.token_type == 'ERC721'
                        ,
                        or_(
                            Tokens.name.ilike(f"%{query_string}%"),
                            Tokens.symbol.ilike(f"%{query_string}%"),
                        )
                    )
                )
                .limit(5)
                .all()
            )
            erc1155_tokens = (
                db.session.query(Tokens)
                .with_entities(
                    Tokens.name,
                    Tokens.symbol,
                    Tokens.address,
                )
                .filter(
                    and_(
                        Tokens.token_type == 'ERC1155'
                        ,
                        or_(
                            Tokens.name.ilike(f"%{query_string}%"),
                            Tokens.symbol.ilike(f"%{query_string}%"),
                        )
                    )
                )
                .limit(5)
                .all()
            )

            for token in erc20_tokens + erc721_tokens + erc1155_tokens:
                search_result.append(
                    {
                        "token_name": token.name,
                        "token_symbol": token.symbol,
                        "token_address": "0x" + token.address.hex(),
                        "token_logo_url": "",
                        "type": "token",
                    }
                )

            ens_match_wallets = (
                db.session.query(WalletAddresses)
                .filter(
                    WalletAddresses.ens_name.ilike(f"%{query_string}%"),
                )
                .limit(5)
                .all()
            )
            for wallet in ens_match_wallets:
                search_result.append(
                    {
                        "wallet_address": '0x' + wallet.address.hex(),
                        "ens_name": wallet.ens_name,
                        "type": "address",
                    }
                )

        return search_result, 200


@explorer_namespace.route("/v1/explorer/internal_transactions")
class ExplorerInternalTransactions(Resource):
    @cache.cached(timeout=60, query_string=True)
    def get(self):
        page_index = int(flask.request.args.get("page", 1))
        page_size = int(flask.request.args.get("size", PAGE_SIZE))
        if page_index <= 0 or page_size <= 0:
            raise APIError("Invalid page or size", code=400)

        address = flask.request.args.get("address")
        block = flask.request.args.get("block", None)

        if page_index * page_size > MAX_INTERNAL_TRANSACTION:
            raise APIError(
                f"Showing the last {MAX_INTERNAL_TRANSACTION} records only",
                code=400,
            )

        filter_condition = True
        if address:
            address = bytes.fromhex(address.lower()[2:])
            filter_condition = or_(
                ContractInternalTransactions.from_address == address,
                ContractInternalTransactions.to_address == address,
            )
        elif block:
            filter_condition = ContractInternalTransactions.block_number == block

        transactions = (
            db.session.query(ContractInternalTransactions)
            .order_by(
                ContractInternalTransactions.block_number.desc(),
                ContractInternalTransactions.transaction_index.desc(),
            )
            .filter(filter_condition)
            .limit(page_size)
            .offset((page_index - 1) * page_size)
            .all()
        )
        # Slow - 300ms
        if (len(transactions) > 0 or page_index == 1) and len(transactions) < page_size:
            total_records = (page_index - 1) * page_size + len(transactions)
        elif filter_condition == True:
            total_records = get_total_row_count("contract_internal_transactions")
        else:
            total_records = (
                db.session.query(
                    ContractInternalTransactions.block_number,
                    ContractInternalTransactions.transaction_index,
                )
                .filter(filter_condition)
                .count()
            )

        transaction_list = []
        address_list = []
        for transaction in transactions:
            transaction_json = as_dict(transaction)
            transaction_json["from_address_is_contract"] = False
            transaction_json["to_address_is_contract"] = False
            transaction_json["value"] = format_coin_value_with_unit(transaction.value,
                                                                    app_config.token_configuration.native_token)
            transaction_list.append(transaction_json)
            address_list.append(transaction.from_address)
            address_list.append(transaction.to_address)

        # Find contract
        contracts = (
            db.session.query(Contracts)
            .with_entities(Contracts.address)
            .filter(Contracts.address.in_(list(set(address_list))))
            .all()
        )
        contract_list = set(map(lambda x: x.address, contracts))

        for transaction_json in transaction_list:
            if transaction_json["to_address"] in contract_list:
                transaction_json["to_address_is_contract"] = True
            if transaction_json["from_address"] in contract_list:
                transaction_json["from_address_is_contract"] = True

        return {
            "data": transaction_list,
            "total": total_records,
            "max_display": min(total_records, MAX_INTERNAL_TRANSACTION),
            "page": page_index,
            "size": page_size,
        }, 200


@explorer_namespace.route("/v1/explorer/transactions")
class ExplorerTransactions(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self):
        page_index = int(flask.request.args.get("page", 1))
        page_size = int(flask.request.args.get("size", 25))
        if page_index <= 0 or page_size <= 0:
            raise APIError("Invalid page or size", code=400)

        if page_index * page_size > MAX_TRANSACTION:
            raise APIError(f"Showing the last {MAX_TRANSACTION} records only", code=400)

        batch = flask.request.args.get("batch", None)
        state_batch = flask.request.args.get("state_batch", None)
        da_batch = flask.request.args.get("da_batch", None)
        block = flask.request.args.get("block", None)
        address = flask.request.args.get("address", None)
        date = flask.request.args.get("date", None)

        has_filter = False
        if batch or block or state_batch or da_batch or address or date:
            has_filter = True
            if page_index * page_size > MAX_TRANSACTION_WITH_CONDITION:
                raise APIError(
                    f"Showing the last {MAX_TRANSACTION_WITH_CONDITION} records only",
                    code=400,
                )

        filter_condition = True
        total_records = 0

        if block:
            if block.isnumeric():
                chain_block = Blocks.query.filter(Blocks.number == block).first()
                if not chain_block:
                    raise APIError("Block not exist", code=400)
                total_records = chain_block.transactions_count
                filter_condition = Transactions.block_number == block
            else:
                block = bytes.fromhex(block.lower()[2:])
                chain_block = Blocks.query.get(block)
                if not chain_block:
                    raise APIError("Block not exist", code=400)
                total_records = chain_block.transactions_count
                filter_condition = Transactions.block_hash == block

        elif address:
            address_str = address.lower()
            address_bytes = bytes.fromhex(address_str[2:])
            filter_condition = or_(
                Transactions.from_address == address_bytes,
                Transactions.to_address == address_bytes,
            )
            total_records = get_address_transaction_cnt(address_str)
        elif date:
            date_object = datetime.strptime(date, "%Y%m%d")
            start_time = date_object
            end_time = start_time + timedelta(days=1)

            filter_condition = (Transactions.block_timestamp >= start_time) & (Transactions.block_timestamp < end_time)

        transactions = (
            db.session.query(Transactions)
            .order_by(
                Transactions.block_number.desc(),
                Transactions.transaction_index.desc(),
            )
            .filter(filter_condition)
            .limit(page_size)
            .offset((page_index - 1) * page_size)
            .all()
        )

        if (len(transactions) > 0 or page_index == 1) and len(transactions) < page_size:
            total_records = (page_index - 1) * page_size + len(transactions)

        # Only if has filter and we haven't calculate total transactions, then we query to get total count
        elif has_filter and len(transactions) > 0 and total_records == 0:
            total_records = db.session.query(Transactions.hash).filter(filter_condition).count()
        elif total_records == 0:
            total_records = get_total_txn_count()
        transactions = [as_dict(transaction) for transaction in transactions]
        transaction_list = parse_transactions(transactions)

        return {
            "data": transaction_list,
            "total": total_records,
            "max_display": min(
                (MAX_TRANSACTION_WITH_CONDITION if has_filter else MAX_TRANSACTION),
                total_records,
            ),
            "page": page_index,
            "size": page_size,
        }, 200


# {
#   'components':[
#     {'internalType': 'address', 'name': 'pool', 'type': 'address'},
#     {'internalType': 'bytes', 'name': 'data', 'type': 'bytes'},
#     {'internalType': 'address', 'name': 'callback', 'type': 'address'},
#     {'internalType': 'bytes', 'name': 'callbackData', 'type': 'bytes'}
#   ],
#   'internalType': 'struct IRouter.SwapStep[]',
#   'name': 'steps',
#   'type': 'tuple[]'
# }
def generate_type_str(component):
    if component["type"] == "tuple[]":
        tuple_types = tuple(map(lambda x: generate_type_str(x), component["components"]))
        return "(" + ",".join(tuple_types) + ")[]"
    elif component["type"] == "tuple":
        tuple_types = tuple(map(lambda x: generate_type_str(x), component["components"]))
        return "(" + ",".join(tuple_types) + ")"
    else:
        return component["type"]


@explorer_namespace.route("/v1/explorer/transaction/<hash>")
class ExplorerTransactionDetail(Resource):
    @cache.cached(timeout=60, query_string=True)
    def get(self, hash):
        hash = bytes.fromhex(hash.lower()[2:])
        transaction = db.session.query(Transactions).get(hash)
        if transaction:
            transaction = as_dict(transaction)
            transaction_json = parse_transactions([transaction])[0]

            trace = (
                db.session.query(Traces)
                .with_entities(Traces.error)
                .filter(
                    Traces.transaction_hash == hash,
                    Traces.trace_address == "{}",
                )
                .first()
            )

            # Add trace info to transaction detail
            if trace and trace.error:
                transaction_json["trace_error"] = trace.error

            abi_dict = get_abis_for_method([(transaction['to_address'], transaction_json["method_id"])])

            try:
                if abi_dict:
                    _, contract_function_abi = abi_dict.popitem()
                    data_types = []
                    function_abi_json = json.loads(contract_function_abi.get("function_abi"))
                    for input in function_abi_json["inputs"]:
                        full_type_str = generate_type_str(input)
                        data_types.append(full_type_str)
                        input["full_type_str"] = full_type_str

                    decoded_data, endcoded_data = decode_log_data(data_types, transaction.input[10:])
                    input_data = []
                    full_function_name = ""
                    for index in range(len(function_abi_json["inputs"])):
                        param = function_abi_json["inputs"][index]
                        input_data.append(
                            {
                                "name": param["name"],
                                "data_type": param["full_type_str"],
                                "hex_data": decoded_data[index],
                                "dec_data": endcoded_data[index],
                            }
                        )
                        full_function_name += f"{param['full_type_str']} {param['name']}, "
                    function_name = contract_function_abi.get("function_name")
                    full_function_name = f"{function_name}({full_function_name[:-2]})"
                    transaction_json["input_data"] = input_data
                    transaction_json["function_name"] = function_name
                    transaction_json["function_unsigned"] = contract_function_abi.get("function_unsigned")
                    transaction_json["full_function_name"] = full_function_name
            except Exception as e:
                print(str(e))

            return transaction_json, 200
        else:
            raise APIError("Cannot find transaction with hash", code=400)


@explorer_namespace.route("/v1/explorer/transaction/<hash>/logs")
class ExplorerTransactionLogs(Resource):
    @cache.cached(timeout=360, query_string=True)
    def get(self, hash):
        hash = bytes.fromhex(hash.lower()[2:])
        logs = (
            db.session.query(Logs)
            .filter(Logs.transaction_hash == hash)
            .join(Transactions, Logs.transaction_hash == Transactions.hash)
            .add_columns(Transactions.input)
            .all()
        )
        log_list = parse_log_with_transaction_input_list(logs)

        return {"total": len(log_list), "data": log_list}, 200


@explorer_namespace.route("/v1/explorer/transaction/<hash>/token_transfers")
class ExplorerTransactionTokenTransfers(Resource):
    @cache.cached(timeout=360, query_string=True)
    def get(self, hash):
        hash = bytes.fromhex(hash.lower()[2:])

        erc20_token_transfers = (
            db.session.query(ERC20TokenTransfers)
            .filter(ERC20TokenTransfers.transaction_hash == hash)
            .join(
                Tokens,
                ERC20TokenTransfers.token_address == Tokens.address,
            )
            .add_columns(
                Tokens.name,
                Tokens.symbol,
                Tokens.decimals,
                Tokens.icon_url,
            )
            .all()
        )

        erc721_token_transfers = (
            db.session.query(ERC721TokenTransfers)
            .filter(ERC721TokenTransfers.transaction_hash == hash)
            .join(
                Tokens,
                ERC721TokenTransfers.token_address == Tokens.address,
            )
            .add_columns(
                Tokens.name,
                Tokens.symbol,
            )
            .all()
        )

        # ERC1155
        erc1155_token_transfers = (
            db.session.query(ERC1155TokenTransfers)
            .filter(ERC1155TokenTransfers.transaction_hash == hash)
            .join(
                Tokens,
                ERC1155TokenTransfers.token_address == Tokens.address,
            )
            .add_columns(
                Tokens.name,
                Tokens.symbol,
            )
            .all()
        )

        token_transfer_list = []
        token_transfer_list.extend(process_token_transfer(erc20_token_transfers, "tokentxns"))
        token_transfer_list.extend(process_token_transfer(erc721_token_transfers, "tokentxns-nft"))
        token_transfer_list.extend(process_token_transfer(erc1155_token_transfers, "tokentxns-nft1155"))
        fill_address_display_to_transactions(token_transfer_list)

        return {
            "total": len(token_transfer_list),
            "data": token_transfer_list,
        }, 200


@explorer_namespace.route("/v1/explorer/transaction/<hash>/internal_transactions")
class ExplorerTransactionInternalTransactions(Resource):
    @cache.cached(timeout=360, query_string=True)
    def get(self, hash):
        hash = bytes.fromhex(hash.lower()[2:])

        transactions = (
            db.session.query(ContractInternalTransactions)
            .order_by(
                ContractInternalTransactions.block_number.desc(),
                ContractInternalTransactions.transaction_index.desc(),
            )
            .filter(ContractInternalTransactions.transaction_hash == hash)
            .all()
        )
        transaction_list = []
        address_list = []
        for transaction in transactions:
            transaction_json = as_dict(transaction)
            transaction_json["from_address_is_contract"] = False
            transaction_json["to_address_is_contract"] = False
            transaction_json["value"] = format_coin_value_with_unit(transaction.value,
                                                                    app_config.token_configuration.native_token)
            transaction_list.append(transaction_json)
            address_list.append(transaction.from_address)
            address_list.append(transaction.to_address)

        # Find contract
        contracts = (
            db.session.query(Contracts)
            .with_entities(Contracts.address)
            .filter(Contracts.address.in_(list(set(address_list))))
            .all()
        )
        contract_list = set(map(lambda x: x.address, contracts))

        for transaction_json in transaction_list:
            if transaction_json["to_address"] in contract_list:
                transaction_json["to_address_is_contract"] = True
            if transaction_json["from_address"] in contract_list:
                transaction_json["from_address_is_contract"] = True

        fill_address_display_to_transactions(transaction_list)

        return {"total": len(transaction_list), "data": transaction_list}, 200


@explorer_namespace.route("/v1/explorer/transaction/<hash>/traces")
class ExplorerTransactionInternalTransactions(Resource):
    @cache.cached(timeout=360, query_string=True)
    def get(self, hash):
        def process_data(data):
            if data is None:
                raise APIError("Trace Not Found", code=400)
            function_signature_contracts_set = set()
            addresses_set = set()

            def process_signature_contracts_map_from_trace(obj):
                if isinstance(obj, dict):
                    from_address = obj.get("from_address")
                    to_address = obj.get("to_address")
                    if to_address:
                        addresses_set.add(to_address)
                    if from_address:
                        addresses_set.add(from_address)
                    input = obj.get("input")
                    if to_address and input and len(input) > 10:
                        function_signature_contracts_set.add((to_address, input[:10]))
                    if obj.get("calls"):
                        for call in obj.get("calls"):
                            process_signature_contracts_map_from_trace(call)

            process_signature_contracts_map_from_trace(data)

            abi_map = get_abis_for_method(list(function_signature_contracts_set))

            address_display_map = get_address_display_mapping(addresses_set)

            def convert_hex_to_dec(x):
                if x is None:
                    return 0
                return int(x, 16) if isinstance(x, str) and x.startswith("0x") else x

            def traverse(obj):
                if isinstance(obj, dict):
                    if obj.get("from_address") in address_display_map:
                        obj["from_address_display_name"] = address_display_map.get(obj.get("from_address"))
                    else:
                        obj["from_address_display_name"] = obj.get("from_address")

                    if obj.get("to_address") in address_display_map:
                        obj["to_address_display_name"] = address_display_map.get(obj.get("to_address"))
                    else:
                        obj["to_address_display_name"] = obj.get("to_address")

                    function_name = None
                    function_input, function_output = [], []
                    if obj.get("call_type") == "selfdestruct":
                        function_name = "Selfdestruct"
                    elif obj.get("call_type") in ["create2", "create"]:
                        function_name = "CreateContract"
                    else:
                        input = obj.get("input") or "0x"
                        output = obj.get("output") or "0x"
                        contract_function_abi = abi_map.get((obj.get("to_address"), input[:10]))
                        decode_failed = True
                        if contract_function_abi:
                            function_abi = contract_function_abi.get("function_abi")
                            function_abi_json = json.loads(function_abi)
                            function_name = f"{contract_function_abi.get('function_name')}"
                            try:
                                function_input, function_output = decode_function(
                                    function_abi_json, input[2:], output[2:]
                                )
                                decode_failed = False
                            except Exception as e:
                                logging.error(
                                    f'Error decoding function: {str(e)}, to_address: {obj.get("to_address")}, tx_hash: {hash}, contract_function_abi: {function_abi}'
                                )

                        if decode_failed and obj.get("to_address") and len(input) >= 10:
                            function_name = input[:10]
                            function_input = [
                                {
                                    "name": "call_data",
                                    "value": input[10:],
                                    "type": "string",
                                }
                            ]
                            if len(output) > 2:
                                function_output = (
                                    [
                                        {
                                            "name": "return_data",
                                            "value": output[2:],
                                            "type": "string",
                                        }
                                    ]
                                    if len(output) > 2
                                    else []
                                )
                        else:
                            function_name = "fallback"
                            function_input = (
                                [
                                    {
                                        "name": "call_data",
                                        "value": input[2:],
                                        "type": "string",
                                    }
                                ]
                                if len(input) > 2
                                else []
                            )
                            function_output = []

                        obj["function_name"] = function_name
                        obj["function_input"] = function_input
                        obj["function_output"] = function_output
                    if obj.get("calls"):
                        for call in obj.get("calls"):
                            traverse(call)

            traverse(data)
            return data

        hash = hash.lower()
        if len(hash) != 66 or not all(c in string.hexdigits for c in hash[2:]):
            raise APIError("Invalid transaction hash", code=400)
        try:
            hash = bytes.fromhex(hash[2:])

            traces_row = (
                db.session.query(Traces)
                .filter(Traces.transaction_hash == hash)
                .order_by(Traces.trace_address)
                .all()
            )

            trace = get_debug_trace_transaction(
                [
                    {
                        "from_address": "0x" + trace.from_address.hex(),
                        "to_address": "0x" + trace.to_address.hex(),
                        "value": (
                            "{0:.18f}".format(trace.value / 10 ** 18).rstrip("0").rstrip(".")
                            if trace.value is not None and trace.value != 0
                            else None
                        ),
                        "trace_type": trace.trace_type,
                        "call_type": trace.call_type,
                        "gas": (int(trace.gas) if trace.gas is not None else None),
                        "gasUsed": (int(trace.gas_used) if trace.gas_used is not None else None),
                        "gas_used": (int(trace.gas_used) if trace.gas_used is not None else None),
                        "input": ("0x" + trace.input.hex() if trace.input is not None else None),
                        "output": ("0x" + trace.output.hex() if trace.output is not None else None),
                        "trace_address": str(trace.trace_address).replace('[', '{').replace(']', '}'),
                        "subtraces": trace.subtraces,
                        "error": trace.error,
                        "status": trace.status,
                    }
                    for trace in traces_row
                ]
            )
        except Exception as e:
            raise APIError(str(e), code=400)
        return {"data": process_data(trace)}, 200


@explorer_namespace.route("/v1/explorer/tokens")
class ExplorerTokens(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self):
        page_index = int(flask.request.args.get("page", 1))
        page_size = int(flask.request.args.get("size", 25))
        is_verified = flask.request.args.get("is_verified", "true") in [
            "True",
            "true",
            "TRUE",
        ]
        if page_index <= 0 or page_size <= 0:
            raise APIError("Invalid page or size", code=400)
        # erc20, erc721, erc1155
        type = flask.request.args.get("type")
        if type == "erc20":
            sort = flask.request.args.get("sort", "market_cap")
            order = flask.request.args.get("order", "desc")
            if sort not in [
                "market_cap",
                "volume_24h",
                "holder_count",
                "price",
                "on_chain_market_cap",
            ]:
                raise APIError("Invalid sort", code=400)
            if order not in ["asc", "desc"]:
                raise APIError("Invalid order", code=400)
            order_expression = getattr(Tokens, sort)
            if order == "desc":
                order_expression = order_expression.desc()
            else:
                order_expression = order_expression.asc()
            order_expression = nullslast(order_expression)
            tokens = (
                db.session.query(Tokens)
                .with_entities(
                    Tokens.address,
                    Tokens.name,
                    Tokens.symbol,
                    Tokens.icon_url,
                    Tokens.total_supply,
                    Tokens.decimals,
                    Tokens.price,
                    Tokens.description,
                    Tokens.volume_24h,
                    Tokens.market_cap,
                    Tokens.on_chain_market_cap,
                    Tokens.holder_count,
                )
                .filter(and_(Tokens.is_verified == is_verified if is_verified else 1 == 1),
                        Tokens.token_type == 'ERC20')
                .order_by(order_expression)
                .limit(page_size)
                .offset((page_index - 1) * page_size)
                .all()
            )

            token_list = [
                {
                    "address": '0x' + x.address.hex(),
                    "name": x.name,
                    "symbol": x.symbol,
                    "logo": x.icon_url,
                    "description": x.description,
                    "total_supply": (
                        int(x.total_supply) * 10 ** (0 - int(x.decimals)) if x.total_supply is not None else None
                    ),
                    "volume_24h": (round(x.volume_24h, 2) if x.volume_24h is not None else None),
                    "market_cap": (round(x.market_cap, 2) if x.market_cap is not None else None),
                    "on_chain_market_cap": (
                        round(x.on_chain_market_cap, 2) if x.on_chain_market_cap is not None else None
                    ),
                    "holder_count": x.holder_count,
                    "price": (round(x.price, 4) if x.price is not None else None),
                }
                for x in tokens
            ]

            if is_verified:
                total_records = Tokens.query.filter(
                    and_(Tokens.is_verified == is_verified, Tokens.token_type == 'ERC20')).count()
            else:
                total_records = Tokens.query.filter(Tokens.token_type == 'ERC20').count()

        elif type == "erc721":
            sort = flask.request.args.get("sort", "holder_count")
            order = flask.request.args.get("order", "desc")
            if sort not in ["holder_count", "transfer_count"]:
                raise APIError("Invalid sort", code=400)
            if order not in ["asc", "desc"]:
                raise APIError("Invalid order", code=400)
            order_expression = getattr(Tokens, sort)
            if order == "desc":
                order_expression = order_expression.desc()
            else:
                order_expression = order_expression.asc()
            order_expression = nullslast(order_expression)
            tokens = (
                db.session.query(Tokens)
                .with_entities(
                    Tokens.address,
                    Tokens.name,
                    Tokens.symbol,
                    Tokens.total_supply,
                    Tokens.holder_count,
                    Tokens.transfer_count,
                )
                .filter(Tokens.token_type == 'ERC721')
                .order_by(order_expression)
                .limit(page_size)
                .offset((page_index - 1) * page_size)
                .all()
            )
            total_records = Tokens.query.filter(Tokens.token_type == 'ERC721').count()

            token_list = [
                {
                    "address": '0x' + x.address.hex(),
                    "name": x.name,
                    "symbol": x.symbol,
                    "total_supply": (int(x.total_supply) if x.total_supply is not None else None),
                    "holder_count": x.holder_count,
                    "transfer_count": x.transfer_count,
                }
                for x in tokens
            ]

        elif type == "erc1155":
            sort = flask.request.args.get("sort", "holder_count")
            order = flask.request.args.get("order", "desc")
            if sort not in ["holder_count", "transfer_count"]:
                raise APIError("Invalid sort", code=400)
            if order not in ["asc", "desc"]:
                raise APIError("Invalid order", code=400)
            order_expression = getattr(Tokens, sort)
            if order == "desc":
                order_expression = order_expression.desc()
            else:
                order_expression = order_expression.asc()
            order_expression = nullslast(order_expression)
            tokens = (
                db.session.query(Tokens)
                .with_entities(
                    Tokens.address,
                    Tokens.name,
                    Tokens.symbol,
                    Tokens.total_supply,
                    Tokens.holder_count,
                    Tokens.transfer_count,
                )
                .filter(Tokens.token_type == 'ERC1155')
                .order_by(order_expression)
                .limit(page_size)
                .offset((page_index - 1) * page_size)
                .all()
            )
            total_records = Tokens.query.filter(Tokens.token_type == 'ERC1155').count()
            token_list = [
                {
                    "address": '0x' + x.address.hex(),
                    "name": x.name,
                    "symbol": x.symbol,
                    "total_supply": (int(x.total_supply) if x.total_supply is not None else None),
                    "holder_count": x.holder_count,
                    "transfer_count": x.transfer_count,
                }
                for x in tokens
            ]
        else:
            raise APIError("Invalid type", code=400)

        return {
            "page": page_index,
            "size": page_size,
            "total": total_records,
            "data": token_list,
        }, 200


@explorer_namespace.route("/v1/explorer/token_transfers")
class ExplorerTokenTransfers(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self):
        page_index = int(flask.request.args.get("page", 1))
        page_size = int(flask.request.args.get("size", 25))
        if page_index <= 0 or page_size <= 0:
            raise APIError("Invalid page or size", code=400)
        # tokentxns, tokentxns-nft, tokentxns-nft1155
        type = flask.request.args.get("type")

        if page_index * page_size > MAX_TOKEN_TRANSFER:
            raise APIError(f"Showing the last {MAX_TOKEN_TRANSFER} records only", code=400)

        address = flask.request.args.get("address", None)
        token_address = flask.request.args.get("token_address", None)

        filter_condition = True
        if address:
            address_str = address.lower()
            address_bytes = bytes.fromhex(address_str[2:])
            if type == "tokentxns":
                filter_condition = or_(
                    ERC20TokenTransfers.from_address == address_bytes,
                    ERC20TokenTransfers.to_address == address_bytes,
                )
            elif type == "tokentxns-nft":
                filter_condition = or_(
                    ERC721TokenTransfers.from_address == address_bytes,
                    ERC721TokenTransfers.to_address == address_bytes,
                )
            elif type == "tokentxns-nft1155":
                filter_condition = or_(
                    ERC1155TokenTransfers.from_address == address_bytes,
                    ERC1155TokenTransfers.to_address == address_bytes,
                )
            total_count = get_address_token_transfer_cnt(type, filter_condition, address_str)
        elif token_address:
            token_address = bytes.fromhex(token_address.lower()[2:])
            if type == "tokentxns":
                filter_condition = ERC20TokenTransfers.token_address == token_address
            elif type == "tokentxns-nft":
                filter_condition = ERC721TokenTransfers.token_address == token_address
            elif type == "tokentxns-nft1155":
                filter_condition = ERC1155TokenTransfers.token_address == token_address
            total_count = get_token_address_token_transfer_cnt(type, token_address)
        else:
            total_count = get_total_row_count(type_to_token_transfer_table(type).__tablename__)

        token_transfers, _ = get_raw_token_transfers(type, filter_condition, page_index, page_size, is_count=False)

        token_transfer_list = parse_token_transfers(type, token_transfers)
        return {
            "page": page_index,
            "size": page_size,
            "total": total_count,
            "max_display": MAX_TOKEN_TRANSFER,
            "data": token_transfer_list,
        }, 200


@explorer_namespace.route("/v1/explorer/blocks")
class ExplorerBlocks(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self):
        page_index = int(flask.request.args.get("page", 1))
        page_size = int(flask.request.args.get("size", 25))
        if page_index <= 0 or page_size <= 0:
            raise APIError("Invalid page or size", code=400)

        state_batch = flask.request.args.get("state_batch", None)
        batch = flask.request.args.get("batch", None)

        if state_batch is None and batch is None:
            latest_block = (
                db.session.query(Blocks).with_entities(Blocks.number).order_by(Blocks.number.desc()).first()
            )

            total_blocks = latest_block.number if latest_block else 0

            end_block = total_blocks - (page_index - 1) * page_size
            start_block = end_block - page_size + 1
            start_block = max(0, start_block)

            blocks = (
                db.session.query(Blocks)
                .filter(Blocks.number.between(start_block, end_block))
                .order_by(Blocks.number.desc())
                .all()
            )

            block_list = [as_dict(block) for block in blocks]

            return {
                "data": block_list,
                "total": total_blocks,
                "page": page_index,
                "size": page_size,
            }, 200

        filter_condition = True
        total_blocks = 0
        blocks = (
            db.session.query(Blocks)
            .filter(filter_condition)
            .order_by(Blocks.number.desc())
            .limit(page_size)
            .offset((page_index - 1) * page_size)
            .all()
        )
        block_list = []
        for block in blocks:
            block_list.append(as_dict(block))

        if total_blocks == 0 and len(block_list) > 0:
            lastest_block = (
                db.session.query(Blocks)
                .with_entities(Blocks.number, Blocks.timestamp)
                .order_by(Blocks.number.desc())
                .first()
            )
            total_blocks = lastest_block.number

        pass
        return {
            "data": block_list,
            "total": total_blocks,
            "page": page_index,
            "size": page_size,
        }, 200


@explorer_namespace.route("/v1/explorer/block/<number_or_hash>")
class ExplorerBlockDetail(Resource):
    @cache.cached(timeout=1800, query_string=True)
    def get(self, number_or_hash):
        if number_or_hash.isnumeric():
            number = int(number_or_hash)
            block = db.session.query(Blocks).filter(Blocks.number == int(number)).first()
        else:
            hash = bytes.fromhex(number_or_hash.lower()[2:])
            block = db.session.query(Blocks).filter(Blocks.hash == hash).first()

        if block:
            block_json = as_dict(block)
            # Need additional data eth_price, block time, internal_transaction_count
            internal_transaction_count = (
                db.session.query(ContractInternalTransactions)
                .filter(ContractInternalTransactions.block_number == block.number)
                .count()
            )
            block_json["internal_transaction_count"] = internal_transaction_count

            block_json["gas_fee_token_price"] = "{0:.2f}".format(
                get_token_price(app_config.token_configuration.gas_fee_token, block.timestamp)
            )

            earlier_block_number = max(block.number - 1, 1)
            earlier_block = (
                db.session.query(Blocks)
                .with_entities(Blocks.number, Blocks.timestamp)
                .filter(Blocks.number == earlier_block_number)
                .first()
            )
            block_json["seconds_since_last_block"] = block.timestamp.timestamp() - earlier_block.timestamp.timestamp()

            lastest_block = (
                db.session.query(Blocks).with_entities(Blocks.number).order_by(Blocks.number.desc()).first()
            )
            block_json["is_last_block"] = lastest_block.number == block.number
            return block_json, 200
        else:
            raise APIError("Cannot find block with block number or block hash", code=400)


@explorer_namespace.route("/v1/explorer/address/<address>/profile")
class ExplorerAddressProfile(Resource):
    @cache.cached(timeout=60, query_string=True)
    def get(self, address):
        address_str = address.lower()
        address_bytes = bytes.fromhex(address_str[2:])
        NATIVE_TOKEN_PRICE = get_token_price(app_config.token_configuration.native_token)

        native_token_balance = get_balance(address_str)
        profile_json = {
            "balance": "{0:.18f}".format(native_token_balance / 10 ** 18).rstrip("0").rstrip("."),
            "native_token_price": "{0:.2f}".format(NATIVE_TOKEN_PRICE),
            "balance_dollar": "{0:.2f}".format(native_token_balance * Decimal(NATIVE_TOKEN_PRICE) / 10 ** 18),
            "is_contract": False,
            "is_token": False,
        }

        contract = db.session.query(Contracts).filter(Contracts.address == address_bytes).first()
        if contract:
            profile_json["is_contract"] = True
            profile_json["contract_creator"] = '0x' + contract.contract_creator.hex()
            profile_json["transaction_hash"] = '0x' + contract.transaction_hash.hex()
            profile_json["is_verified"] = contract.is_verified
            profile_json["is_proxy"] = contract.is_proxy
            profile_json["implementation_contract"] = '0x' + contract.implementation_contract.hex() \
                if contract.implementation_contract else None
            profile_json["verified_implementation_contract"] = '0x' + contract.verified_implementation_contract.hex() \
                if contract.verified_implementation_contract else None
            deployed_code = contract.deployed_code or get_sha256_hash(get_code(address_str))
            addresses = get_similar_addresses(deployed_code)
            profile_json["similar_verified_addresses"] = [add for add in addresses if add != address_str]

            token, type = get_token_by_address(address_bytes)

            if token:
                profile_json["is_token"] = True
                profile_json["token_type"] = type
                profile_json["token_name"] = token.name or "Unknown Token"
                profile_json["token_symbol"] = token.symbol or "UNKNOWN"
                profile_json["token_logo_url"] = token.icon_url or app_config.get_default_token_image_url()

        # "block_validated": 1
        return profile_json


@explorer_namespace.route("/v1/explorer/address/<address>/token_holdings")
@explorer_namespace.route("/v2/explorer/address/<address>/token_holdings")
class ExplorerAddressTokenHoldingsV2(Resource):
    @cache.cached(timeout=360, query_string=True)
    def get(self, address):
        address = address.lower()
        address_bytes = bytes.fromhex(address[2:])
        subquery = (
            db.session.query(
                AddressTokenBalances.token_address,
                AddressTokenBalances.balance,
                AddressTokenBalances.token_id,
                AddressTokenBalances.token_type,
                func.row_number()
                .over(
                    partition_by=(
                        AddressTokenBalances.token_address,
                        AddressTokenBalances.token_id,
                    ),
                    order_by=[
                        AddressTokenBalances.block_timestamp.desc(),
                        AddressTokenBalances.block_number.desc(),
                    ],
                )
                .label("rn"),
            )
            .filter(AddressTokenBalances.address == address_bytes)
            .subquery()
        )

        # Left join with other token tables
        result = (
            db.session.query(
                subquery,
                func.coalesce(Tokens.name, Tokens.name, Tokens.name).label("name"),
                func.coalesce(
                    Tokens.symbol,
                    Tokens.symbol,
                    Tokens.symbol,
                ).label("symbol"),
                func.coalesce(Tokens.icon_url, Tokens.icon_url, Tokens.icon_url).label("logo"),
                Tokens.decimals.label("decimals"),
            )
            .outerjoin(
                Tokens,
                subquery.c.token_address == Tokens.address,
            )
            .filter(subquery.c.rn == 1, subquery.c.balance > 0)
            .order_by(subquery.c.token_type)
            .all()
        )
        token_holder_list = []
        for token_holder in result:
            token_holder_list.append(
                {
                    "token_address": '0x' + token_holder.token_address.hex(),
                    "balance": "{0:.6f}".format((token_holder.balance / 10 ** (token_holder.decimals or 0)))
                    .rstrip("0")
                    .rstrip("."),
                    "token_id": int(token_holder.token_id) if token_holder.token_id else None,
                    "token_name": token_holder.name or "Unknown Token",
                    "token_symbol": token_holder.symbol or "UNKNOWN",
                    "token_logo_url": token_holder.logo or app_config.get_default_token_image_url(),
                    "type": {
                        "ERC20": "tokentxns",
                        "ERC721": "tokentxns-nft",
                        "ERC1155": "tokentxns-nft1155",
                    }.get(token_holder.token_type),
                }
            )

        # Add inscriptions
        # add_inscription_holdings()

        return {"data": token_holder_list, "total": len(token_holder_list)}


@explorer_namespace.route("/v1/explorer/address/<address>/transactions")
class ExplorerAddressTransactions(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self, address):
        address = address.lower()
        address_bytes = bytes.fromhex(address[2:])

        transactions = (
            db.session.query(Transactions)
            .order_by(
                Transactions.block_number.desc(),
                Transactions.transaction_index.desc(),
            )
            .filter(
                or_(
                    Transactions.from_address == address_bytes,
                    Transactions.to_address == address_bytes,
                )
            )
            .limit(PAGE_SIZE)
            .all()
        )

        total_count = len(transactions) if len(transactions) < PAGE_SIZE else PAGE_SIZE
        # if len(transactions) < PAGE_SIZE:
        #     total_count = len(transactions)
        # else:
        #     last_timestamp = db.session.query(
        #         func.max(ScheduledWalletCountMetadata.last_data_timestamp)
        #     ).scalar()
        #     recently_txn_count = (
        #         db.session.query(Transactions.hash)
        #         .filter(
        #             and_(
        #                 (Transactions.block_timestamp >= last_timestamp.date() if last_timestamp is not None else True),
        #                 or_(
        #                     Transactions.from_address == address_bytes,
        #                     Transactions.to_address == address_bytes,
        #                 ),
        #             )
        #         )
        #         .count()
        #     )
        #     result = (
        #         db.session.query(WalletAddresses)
        #         .with_entities(WalletAddresses.txn_cnt)
        #         .filter(WalletAddresses.address == address)
        #         .first()
        #     )
        #     past_txn_count = 0 if not result else result[0]
        #     total_count = past_txn_count + recently_txn_count

        transactions = [as_dict(transaction) for transaction in transactions]
        transaction_list = parse_transactions(transactions)

        return {
            "data": transaction_list,
            "total": total_count,
        }, 200


@explorer_namespace.route("/v1/explorer/address/<address>/token_transfers")
class ExplorerAddressTokenTransfers(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self, address):
        address = address.lower()
        address_bytes = bytes.fromhex(address[2:])
        type = flask.request.args.get("type")

        if type == "tokentxns":
            condition = or_(
                ERC20TokenTransfers.from_address == address_bytes,
                ERC20TokenTransfers.to_address == address_bytes,
            )
        elif type == "tokentxns-nft":
            condition = or_(
                ERC721TokenTransfers.from_address == address_bytes,
                ERC721TokenTransfers.to_address == address_bytes,
            )
        elif type == "tokentxns-nft1155":
            condition = or_(
                ERC1155TokenTransfers.from_address == address_bytes,
                ERC1155TokenTransfers.to_address == address_bytes,
            )
        else:
            raise APIError("Invalid type", code=400)

        token_transfers, total_count = get_raw_token_transfers(type, condition, 1, PAGE_SIZE, is_count=False)

        total_count = get_address_token_transfer_cnt(type, condition, address)
        token_transfer_list = parse_token_transfers(type, token_transfers)

        return {
            "total": total_count,
            "data": token_transfer_list,
            "type": type,
        }, 200


@explorer_namespace.route("/v1/explorer/address/<address>/internal_transactions")
class ExplorerAddressInternalTransactions(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self, address):
        address = address.lower()
        address_bytes = bytes.fromhex(address[2:])
        transactions = (
            db.session.query(ContractInternalTransactions)
            .order_by(
                ContractInternalTransactions.block_number.desc(),
                ContractInternalTransactions.transaction_index.desc(),
            )
            .filter(
                or_(
                    ContractInternalTransactions.from_address == address_bytes,
                    ContractInternalTransactions.to_address == address_bytes,
                )
            )
            .limit(PAGE_SIZE)
            .all()
        )
        if len(transactions) < PAGE_SIZE:
            total_count = len(transactions)
        else:
            total_count = (
                db.session.query(ContractInternalTransactions)
                .filter(
                    or_(
                        ContractInternalTransactions.from_address == address_bytes,
                        ContractInternalTransactions.to_address == address_bytes,
                    )
                )
                .count()
            )
        transaction_list = []
        address_list = []
        for transaction in transactions:
            transaction_json = as_dict(transaction)
            transaction_json["from_address_is_contract"] = False
            transaction_json["to_address_is_contract"] = False
            transaction_json["value"] = format_coin_value_with_unit(transaction.value,
                                                                    app_config.token_configuration.native_token)
            transaction_list.append(transaction_json)
            address_list.append(transaction.from_address)
            address_list.append(transaction.to_address)

        # Find contract
        contracts = (
            db.session.query(Contracts)
            .with_entities(Contracts.address)
            .filter(Contracts.address.in_(list(set(address_list))))
            .all()
        )
        contract_list = set(map(lambda x: x.address, contracts))

        for transaction_json in transaction_list:
            if transaction_json["to_address"] in contract_list:
                transaction_json["to_address_is_contract"] = True
            if transaction_json["from_address"] in contract_list:
                transaction_json["from_address_is_contract"] = True

        return {"total": total_count, "data": transaction_list}, 200


@explorer_namespace.route("/v1/explorer/address/<address>/logs")
class ExplorerAddressLogs(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self, address):
        address = address.lower()
        address_bytes = bytes.fromhex(address[2:])

        logs = (
            db.session.query(Logs)
            .filter(Logs.address == address_bytes)
            .join(Transactions, Logs.transaction_hash == Transactions.hash)
            .add_columns(Transactions.input)
            .order_by(
                Logs.block_number.desc(),
                Logs.log_index.desc(),
            )
            .limit(25)
            .all()
        )
        log_list = parse_log_with_transaction_input_list(logs)

        return {"total": len(logs), "data": log_list}, 200


def get_token_by_address(address):
    token_type = None
    token = db.session.query(Tokens).filter(Tokens.address == address).first()
    if token.token_type == 'ERC20':
        token_type = "tokentxns"
    elif token.token_type == 'ERC721':
        token_type = "tokentxns-nft"
    elif token.token_type == 'ERC1155':
        token_type = "tokentxns-nft1155"
    return token, token_type


@explorer_namespace.route("/v1/explorer/token/<address>/profile")
class ExplorerTokenProfile(Resource):
    @cache.cached(timeout=60, query_string=True)
    def get(self, address):
        address = address.lower()
        address_bytes = bytes.fromhex(address[2:])

        token, type = get_token_by_address(address_bytes)

        if not token:
            raise APIError("Token not found", code=400)

        extra_erc20_token_info = {}
        extra_token_info = {}
        if type == "tokentxns":
            extra_erc20_token_info = {
                "token_price": token.price,
                "token_previous_price": token.previous_price,
                "decimals": float(token.decimals),
                "total_supply": "{0:.6f}".format(token.total_supply / (10 ** token.decimals) or 0)
                .rstrip("0")
                .rstrip("."),
                "token_market_cap": token.market_cap,
                "token_on_chain_market_cap": token.on_chain_market_cap,
                "previous_price": token.previous_price,
            }
            if token.gecko_id:
                extra_erc20_token_info["gecko_url"] = f"https://www.coingecko.com/en/coins/{token.gecko_id}"
            if token.cmc_slug:
                extra_erc20_token_info["cmc_url"] = f"https://coinmarketcap.com/currencies/{token.cmc_slug}/"
        token_info = {
            "token_name": token.name,
            "token_checksum_address": to_checksum_address(token.address),
            "token_address": "0x" + token.address.hex(),
            "token_symbol": token.symbol,
            "token_logo_url": token.icon_url,
            "token_urls": token.urls,
            "social_medias": token.urls,
            "token_description": token.description,
            "total_supply": "{:f}".format(token.total_supply or 0),
            "total_holders": token.holder_count,
            "total_transfers": get_token_address_token_transfer_cnt(type, address_bytes),
            "type": type,
        }
        token_info.update(extra_token_info)

        return {**token_info, **extra_erc20_token_info}


@explorer_namespace.route("/v1/explorer/token/<address>/token_transfers")
class ExplorerTokenTokenTransfers(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self, address):
        address = address.lower()
        address_bytes = bytes.fromhex(address[2:])

        token, type = get_token_by_address(address_bytes)
        if not token:
            raise APIError("Token not found", code=400)

        if type == "tokentxns":
            condition = ERC20TokenTransfers.token_address == address_bytes
        elif type == "tokentxns-nft":
            condition = ERC721TokenTransfers.token_address == address_bytes
        elif type == "tokentxns-nft1155":
            condition = ERC1155TokenTransfers.token_address == address_bytes
        else:
            raise APIError("Invalid type", code=400)

        token_transfers, total_count = get_raw_token_transfers(type, condition, 1, PAGE_SIZE, is_count=False)

        total_count = get_token_address_token_transfer_cnt(type, address_bytes)

        token_transfer_list = parse_token_transfers(type, token_transfers)
        return {
            "total": total_count,
            "data": token_transfer_list,
            "type": type,
        }, 200


@explorer_namespace.route("/v2/explorer/token/<address>/top_holders")
class ExplorerTokenTopHolders(Resource):
    @cache.cached(timeout=360, query_string=True)
    def get(self, address):
        address = address.lower()
        address_bytes = bytes.fromhex(address[2:])

        page_index = int(flask.request.args.get("page", 1))
        page_size = int(flask.request.args.get("size", PAGE_SIZE))
        if page_index <= 0 or page_size <= 0:
            raise APIError("Invalid page or size", code=400)

        token, type = get_token_by_address(address_bytes)

        if not token:
            raise APIError("Token not found", code=400)

        if type == "tokentxns":
            top_holders = (
                db.session.query(
                    ERC20TokenHolders.balance_of,
                    ERC20TokenHolders.wallet_address,
                )
                .filter(
                    ERC20TokenHolders.token_address == address_bytes,
                    ERC20TokenHolders.balance_of > 0,
                )
                .order_by(ERC20TokenHolders.balance_of.desc())
                .limit(page_size)
                .offset((page_index - 1) * page_size)
                .all()
            )
            total_records = (
                db.session.query(ERC20TokenHolders.wallet_address)
                .filter(
                    ERC20TokenHolders.token_address == address_bytes,
                    ERC20TokenHolders.balance_of > 0,
                )
                .count()
            )

        elif type == "tokentxns-nft":
            top_holders = (
                db.session.query(
                    ERC721TokenHolders.balance_of,
                    ERC721TokenHolders.wallet_address,
                )
                .filter(
                    ERC721TokenHolders.token_address == address_bytes,
                    ERC721TokenHolders.balance_of > 0,
                )
                .order_by(ERC721TokenHolders.balance_of.desc())
                .limit(page_size)
                .offset((page_index - 1) * page_size)
                .all()
            )
            total_records = (
                db.session.query(ERC721TokenHolders.wallet_address)
                .filter(
                    ERC721TokenHolders.token_address == address_bytes,
                    ERC721TokenHolders.balance_of > 0,
                )
                .count()
            )
        elif type == "tokentxns-nft1155":
            top_holders = (
                db.session.query(
                    ERC1155TokenHolders.wallet_address,
                    func.sum(ERC1155TokenHolders.balance_of).label("balance_of"),
                )
                .filter(
                    ERC1155TokenHolders.token_address == address_bytes,
                    ERC1155TokenHolders.balance_of > 0,
                )
                .group_by(ERC1155TokenHolders.wallet_address)
                .order_by(func.sum(ERC1155TokenHolders.balance_of).desc())
                .limit(page_size)
                .offset((page_index - 1) * page_size)
                .all()
            )
            total_records = (
                db.session.query(ERC1155TokenHolders.wallet_address)
                .filter(
                    ERC1155TokenHolders.token_address == address_bytes,
                    ERC1155TokenHolders.balance_of > 0,
                )
                .count()
            )

        token_holder_list = []
        for token_holder in top_holders:
            token_holder_json = {}
            token_holder_json["token_address"] = address
            decimals = 0
            # if type == "tokentxns-nft1155":
            #    token_holder_json["token_id"] = int(token_holder.token_id)
            if type == "tokentxns":
                decimals = token.decimals
            token_holder_json["wallet_address"] = '0x' + token_holder.wallet_address.hex()
            token_holder_json["balance"] = "{0:.6f}".format((token_holder.balance_of / 10 ** (decimals)) or 0)
            token_holder_list.append(token_holder_json)

        return {"data": token_holder_list, "total": total_records}


@explorer_namespace.route("/v1/explorer/token/<address>/top_holders")
class ExplorerTokenTopHolders(Resource):
    @cache.cached(timeout=360, query_string=True)
    def get(self, address):
        address = address.lower()
        address_bytes = bytes.fromhex(address[2:])

        page_index = int(flask.request.args.get("page", 1))
        page_size = int(flask.request.args.get("size", PAGE_SIZE))
        if page_index <= 0 or page_size <= 0:
            raise APIError("Invalid page or size", code=400)

        token, type = get_token_by_address(address_bytes)

        if not token:
            raise APIError("Token not found", code=400)

        if type == "tokentxns":
            top_holders = (
                db.session.query(ERC20TokenHolders)
                .filter(
                    ERC20TokenHolders.token_address == address_bytes,
                    ERC20TokenHolders.balance_of > 0,
                )
                .order_by(ERC20TokenHolders.balance_of.desc())
                .limit(page_size)
                .offset((page_index - 1) * page_size)
                .all()
            )
            total_records = (
                db.session.query(ERC20TokenHolders.wallet_address)
                .filter(
                    ERC20TokenHolders.token_address == address_bytes,
                    ERC20TokenHolders.balance_of > 0,
                )
                .count()
            )

        elif type == "tokentxns-nft":
            top_holders = (
                db.session.query(ERC721TokenHolders)
                .filter(
                    ERC721TokenHolders.token_address == address_bytes,
                    ERC721TokenHolders.balance_of > 0,
                )
                .order_by(ERC721TokenHolders.balance_of.desc())
                .limit(page_size)
                .offset((page_index - 1) * page_size)
                .all()
            )
            total_records = (
                db.session.query(ERC721TokenHolders.wallet_address)
                .filter(
                    ERC721TokenHolders.token_address == address_bytes,
                    ERC721TokenHolders.balance_of > 0,
                )
                .count()
            )
        elif type == "tokentxns-nft1155":
            top_holders = (
                db.session.query(ERC1155TokenHolders)
                .filter(
                    ERC1155TokenHolders.token_address == address_bytes,
                    ERC1155TokenHolders.balance_of > 0,
                )
                .order_by(ERC1155TokenHolders.balance_of.desc())
                .limit(page_size)
                .offset((page_index - 1) * page_size)
                .all()
            )
            total_records = (
                db.session.query(ERC1155TokenHolders.wallet_address)
                .filter(
                    ERC1155TokenHolders.token_address == address_bytes,
                    ERC1155TokenHolders.balance_of > 0,
                )
                .count()
            )

        token_holder_list = []
        for token_holder in top_holders:
            token_holder_json = as_dict(token_holder)
            token_holder_json["balance"] = "{0:.6f}".format(token_holder.balance_of or 0)
            token_holder_list.append(token_holder_json)

        return {"data": token_holder_list, "total": total_records}


@explorer_namespace.route("/v1/explorer/contract/update_info")
@explorer_namespace.route("/v1/socialscan/contract/update_info")
class ExplorerUploadContractInfo(Resource):
    def post(self):
        request_body = flask.request.json
        address = request_body.get("address")
        official_website = request_body.get("official_website")
        social_list = request_body.get("social_list")
        description = request_body.get("description")
        email = request_body.get("email")

        if not address or (not official_website and not social_list and not description and not email):
            raise APIError("Missing required data", code=400)

        address_bytes = bytes.fromhex(address[2:])
        # Check if address exists in ContractsInfo
        contracts = db.session.query(Contracts).filter_by(address=address_bytes).first()

        if not contracts:
            raise APIError("Error address", code=400)

        # Update existing contract info
        if official_website:
            contracts.official_website = official_website
        if social_list:
            contracts.social_list = social_list
        if description:
            contracts.description = description
        if email:
            contracts.email = email
        contracts.update_time = datetime.now()
        db.session.commit()

        return {"message": "Contract info updated successfully"}, 200


@explorer_namespace.route("/v1/explorer/statistics/contract/ranks")
class ExplorerStatisticsContractData(Resource):
    statistics_sql_mapping = {
        "transactions_received": lambda session, limit: session.query(
            Transactions.to_address.label("address"),
            func.count().label("transaction_count"),
            StatisticsWalletAddresses.tag,
        )
        .join(
            StatisticsWalletAddresses,
            cast('0x' + func.encode(Transactions.to_address, 'hex'), VARCHAR) == StatisticsWalletAddresses.address,
            isouter=True,
        )
        .filter(
            Transactions.block_timestamp > datetime.now() - timedelta(days=1),
            Transactions.to_address.in_(session.query(Contracts.address)),
        )
        .group_by(Transactions.to_address, StatisticsWalletAddresses.tag)
        .order_by(func.count().desc())
        .limit(limit)
        .all(),
    }

    @cache.cached(timeout=600, query_string=True)
    def get(self):
        statistics_arg = flask.request.args.get("statistics", None)
        try:
            limit = int(flask.request.args.get("limit", 10))
        except ValueError:
            limit = 10
        if limit > 100:
            raise APIError("Limit should not be greater than 100", code=400)

        if statistics_arg not in self.statistics_sql_mapping:
            raise APIError("Invalid or missing statistics type", code=400)

        result = self.statistics_sql_mapping[statistics_arg](db.session, limit)

        address_list = []
        for row in result:
            address_json = row_to_dict(row)
            address_list.append(address_json)

        return {"data": address_list}, 200


@explorer_namespace.route("/v1/explorer/statistics/address/ranks")
class ExplorerStatisticsAddressData(Resource):
    statistics_sql_mapping = {
        "gas_used": lambda session, limit: session.query(
            Transactions.from_address.label("address"),
            func.sum(Transactions.receipt_gas_used).label("gas_used"),
            StatisticsWalletAddresses.tag,
        )
        .join(
            StatisticsWalletAddresses,
            cast('0x' + func.encode(Transactions.from_address, 'hex'), VARCHAR) == StatisticsWalletAddresses.address,
            isouter=True,
        )
        .filter(Transactions.block_timestamp > datetime.now() - timedelta(days=1))
        .group_by(Transactions.from_address, StatisticsWalletAddresses.tag)
        .order_by(func.sum(Transactions.receipt_gas_used).desc())
        .limit(limit)
        .all(),
        "transactions_sent": lambda session, limit: session.query(
            Transactions.from_address.label("address"),
            func.count().label("transaction_count"),
            StatisticsWalletAddresses.tag,
        )
        .join(
            StatisticsWalletAddresses,
            cast('0x' + func.encode(Transactions.from_address, 'hex'), VARCHAR) == StatisticsWalletAddresses.address,
            isouter=True,
        )
        .filter(Transactions.block_timestamp > datetime.now() - timedelta(days=1))
        .group_by(Transactions.from_address, StatisticsWalletAddresses.tag)
        .order_by(func.count().desc())
        .limit(limit)
        .all(),
    }

    @cache.cached(timeout=600, query_string=True)
    def get(self):
        statistics_arg = flask.request.args.get("statistics", None)
        try:
            limit = int(flask.request.args.get("limit", 10))
        except ValueError:
            limit = 10
        if limit > 100:
            raise APIError("Limit should not be greater than 100", code=400)

        if statistics_arg not in self.statistics_sql_mapping:
            raise APIError("Invalid or missing statistics type", code=400)

        result = self.statistics_sql_mapping[statistics_arg](db.session, limit)

        unique_addresses = ['0x' + row.address.hex() for row in result]
        ens_mapping = get_ens_mapping(unique_addresses)
        address_list = []
        for row in result:
            address_json = row_to_dict(row)
            address_json["ens_name"] = ens_mapping.get(address_json["address"])
            address_list.append(address_json)

        return {"data": address_list}, 200


@explorer_namespace.route("/v1/explorer/chart-data/daily")
class ExplorerChartDataDaily(Resource):
    @cache.cached(timeout=3600, query_string=True)
    def get(self):
        metrics_arg = flask.request.args.get("metrics", "")
        metrics_list = [metric.strip() for metric in metrics_arg.split(",") if metric.strip()]

        if not metrics_list:
            return {"error": "No metrics provided."}, 400

        raw_start_date = flask.request.args.get("start_date")
        raw_end_date = flask.request.args.get("end_date")

        if raw_start_date is None:
            start_date = date(1900, 1, 1)
        else:
            try:
                start_date = datetime.strptime(raw_start_date, "%Y-%m-%d").date()
            except ValueError:
                return {"error": "Invalid start_date format. Expected format: YYYY-MM-DD."}, 400

        if raw_end_date is None:
            end_date = date.today() - timedelta(days=1)
        else:
            try:
                end_date = datetime.strptime(raw_end_date, "%Y-%m-%d").date()
            except ValueError:
                return {"error": "Invalid end_date format. Expected format: YYYY-MM-DD."}, 400

        if end_date < start_date:
            return {"error": "end_date should not be earlier than start_date."}, 400

        tables_to_query = {}
        for metric in metrics_list:
            if "." not in metric or len(metric.split(".")) != 2:
                return {"error": f"Invalid metric: {metric}."}, 400
            table_name, field_name = metric.split(".")

            if table_name not in tables_to_query:
                tables_to_query[table_name] = []

            tables_to_query[table_name].append(field_name)

        data_list = {}
        for table_name, fields in tables_to_query.items():
            if table_name == "transaction":
                table = DailyTransactionsAggregates
            elif table_name == "address":
                table = DailyAddressesAggregates
            elif table_name == "block":
                table = DailyBlocksAggregates
            elif table_name == "token":
                table = DailyTokensAggregates
            else:
                return {"error": f"Unknown table name in metric: {metrics_list}."}, 400

            for field in fields:
                if not hasattr(table, field):
                    return {"error": f'Unknown field "{field}" in table "{table_name}".'}, 400

            query = db.session.query(
                getattr(table, "block_date"),
                *(getattr(table, field) for field in fields),
            ).filter(
                and_(
                    table.block_date >= start_date,
                    table.block_date <= end_date,
                )
            )

            for record in query:
                block_date = record[0].isoformat()

                if block_date not in data_list:
                    data_list[block_date] = {"date": block_date}

                for i, field in enumerate(fields):
                    value = record[i + 1]

                    field_type = getattr(table, field).type
                    if isinstance(field_type, sqlalchemy.Numeric):
                        value = float(value) if value is not None else 0

                    data_list[block_date]["{}.{}".format(table_name, field)] = value or 0
        sorted_data = sorted(list(data_list.values()), key=lambda x: x["date"])
        results = {"data": sorted_data}
        return results, 200


# @explorer_namespace.route("/v1/explorer/da_fee_tracker")
# class ExplorerDAFeeTracker(Resource):
#     @cache.cached(timeout=300, query_string=True)
#     def get(self):
#         ## da on ethereum
#         # Cumulative DA Feemake
#         # Fetches the total data size and total L1 DA fee in USD
#         cumulative_da_fee_query = db.session.query(
#             func.coalesce(func.sum(DailyDATransactionsAggregates.data_size), 0).label("total_data_size"),
#             func.coalesce(
#                 func.sum(DailyDATransactionsAggregates.total_transaction_fee_on_l1_usd),
#                 0,
#             ).label("total_l1_da_fee_usd"),
#             func.coalesce(
#                 func.sum(DailyDATransactionsAggregates.estimate_celestia_da_fee_usd),
#                 0,
#             ).label("total_celestia_da_fee_usd"),
#         ).where(DailyDATransactionsAggregates.block_date <= datetime(2023, 12, 15))
#
#         _, _, _ = cumulative_da_fee_query.first() if cumulative_da_fee_query.first() else (0, 0, 0)
#
#         ## da on celestia
#         cumulative_celestia_da_fee_query = db.session.query(
#             func.coalesce(func.sum(DailyCelestiaDaTransactionsAggregates.data_size), 0).label("total_data_size"),
#             func.coalesce(
#                 func.sum(DailyCelestiaDaTransactionsAggregates.celestia_da_fee_usd),
#                 0,
#             ).label("total_l1_da_fee_usd"),
#             func.coalesce(
#                 func.sum(DailyCelestiaDaTransactionsAggregates.estimate_ethereum_da_fee_usd),
#                 0,
#             ).label("total_celestia_da_fee_usd"),
#         ).where(DailyCelestiaDaTransactionsAggregates.block_date > datetime(2023, 12, 15))
#
#         (
#             total_celestia_data_size,
#             actual_total_celestia_da_fee_usd,
#             cumulative_total_l1_da_fee_usd,
#         ) = (
#             cumulative_celestia_da_fee_query.first() if cumulative_celestia_da_fee_query.first() else (0, 0, 0)
#         )
#
#         # Yesterday DA Fee
#         # Fetches the data size and L1 DA fee in USD for the most recent record
#         latest_da_fee_query = (
#             db.session.query(
#                 DailyCelestiaDaTransactionsAggregates.data_size,
#                 DailyCelestiaDaTransactionsAggregates.estimate_ethereum_da_fee_usd,
#                 DailyCelestiaDaTransactionsAggregates.celestia_da_fee_usd,
#             )
#             .filter(DailyCelestiaDaTransactionsAggregates.block_date < datetime.now().date())
#             .order_by(DailyCelestiaDaTransactionsAggregates.block_date.desc())
#         )
#
#         latest_record = latest_da_fee_query.first()
#         latest_data_size = latest_record.data_size if latest_record else 0
#         latest_l1_da_fee_usd = latest_record.estimate_ethereum_da_fee_usd if latest_record else 0
#         latest_estimate_celestia_da_fee_usd = latest_record.celestia_da_fee_usd if latest_record else 0
#
#         # Transaction Count
#         # Fetches the latest and total transaction counts
#         transaction_count_query = (
#             db.session.query(
#                 DailyTransactionsAggregates.cnt.label("latest_transaction_cnt"),
#             )
#             .filter(DailyTransactionsAggregates.block_date < datetime.now().date())
#             .order_by(DailyTransactionsAggregates.block_date.desc())
#         )
#
#         latest_transaction_cnt = (
#             transaction_count_query.first().latest_transaction_cnt if transaction_count_query.first() else 0
#         )
#
#         transaction_count_query = db.session.query(
#             func.sum(DailyTransactionsAggregates.cnt).label("total_transaction_cnt"),
#         ).filter(
#             DailyTransactionsAggregates.block_date > datetime(2023, 12, 15),
#         )
#         total_transaction_cnt = (
#             transaction_count_query.first().total_transaction_cnt if transaction_count_query.first() else 0
#         )
#
#         # DA Fee Data for Last 30 Days
#         data_before_15 = (
#             db.session.query(
#                 DailyDATransactionsAggregates.block_date,
#                 DailyDATransactionsAggregates.data_size,
#                 DailyDATransactionsAggregates.total_transaction_fee_on_l1_usd,
#                 DailyDATransactionsAggregates.estimate_celestia_da_fee_usd,
#             )
#             .filter(
#                 DailyDATransactionsAggregates.block_date <= datetime(2023, 12, 15),
#             )
#             .order_by(DailyDATransactionsAggregates.block_date.desc())
#             .all()
#         )
#
#         data_after_15 = (
#             db.session.query(
#                 DailyCelestiaDaTransactionsAggregates.block_date,
#                 DailyCelestiaDaTransactionsAggregates.data_size,
#                 DailyCelestiaDaTransactionsAggregates.celestia_da_fee_usd,
#                 DailyCelestiaDaTransactionsAggregates.estimate_ethereum_da_fee_usd,
#             )
#             .filter(
#                 DailyCelestiaDaTransactionsAggregates.block_date > datetime(2023, 12, 15),
#             )
#             .order_by(DailyCelestiaDaTransactionsAggregates.block_date.desc())
#             .limit(30)
#             .all()
#         )
#
#         combined_data = data_before_15 + data_after_15
#
#         combined_data.sort(key=lambda x: x.block_date, reverse=False)
#         combined_data = combined_data[-30:]
#         return_data = [
#             {
#                 "date": row.block_date.isoformat(),
#                 "data_size": int(row.data_size),
#                 "transaction_fee_on_l1_usd": float(
#                     row.total_transaction_fee_on_l1_usd
#                     if hasattr(row, "total_transaction_fee_on_l1_usd")
#                     else row.estimate_ethereum_da_fee_usd
#                 ),
#                 "estimate_celestia_da_fee_usd": float(
#                     row.estimate_celestia_da_fee_usd
#                     if hasattr(row, "estimate_celestia_da_fee_usd")
#                     else row.celestia_da_fee_usd
#                 ),
#             }
#             for row in combined_data
#         ]
#
#         last_update_at = (
#                              CelestiaDaTransactions.query.order_by(CelestiaDaTransactions.id.desc()).first().time
#                          ).strftime("%Y-%m-%d %H:%M:%S") + " UTC"
#
#         return {
#             "metrics": {
#                 "total_data_size": int(total_celestia_data_size),
#                 "total_l1_da_fee_usd": float(cumulative_total_l1_da_fee_usd),
#                 "total_transaction_count": int(total_transaction_cnt),
#                 "total_celestia_da_fee_usd": float(actual_total_celestia_da_fee_usd),
#                 "latest_data_size": int(latest_data_size),
#                 "latest_l1_da_fee_usd": float(latest_l1_da_fee_usd),
#                 "latest_transaction_count": int(latest_transaction_cnt),
#                 "latest_estimate_celestia_da_fee_usd": float(latest_estimate_celestia_da_fee_usd),
#             },
#             "data": return_data,
#             "last_updated_at": last_update_at,
#         }, 200


# @explorer_namespace.route("/v1/explorer/da_fee_calculate")
# class ExplorerDAFeeCalculate(Resource):
#     def get(self):
#         transaction_count = flask.request.args.get("transaction_count", "100000")
#         transaction_type = flask.request.args.get("transaction_type", "0")
#         if not transaction_count or not transaction_count.isdigit():
#             raise APIError("Error transaction count", code=400)
#         transaction_count = int(transaction_count)
#         if transaction_count < 0:
#             raise APIError("Error transaction count", code=400)
#
#         if not transaction_type or not transaction_type.isdigit():
#             raise APIError("Error transaction type", code=400)
#         transaction_type = int(transaction_type)
#         if transaction_type < 0 or transaction_type > 6:
#             raise APIError("Error transaction type", code=400)
#
#         estimate_data_size_on_l1 = {
#             0: 140,  # Mixed of Common Blockchain Transactions
#             1: 80,  # ETH Transfer
#             2: 120,  # ERC20 Transfer
#             3: 300,  # ERC20 Swap
#             4: 180,  # ERC721 Mint
#             5: 145,  # ERC721 Transfer
#             6: 500,  # Contract Creation
#         }
#
#         transaction_size_factors = {}
#         base_size = estimate_data_size_on_l1[0]
#
#         for key, value in estimate_data_size_on_l1.items():
#             transaction_size_factors[key] = value / base_size
#
#         # Fetches the latest record
#         latest_da_fee_query = (
#             db.session.query(
#                 DailyDATransactionsAggregates.data_size,
#                 DailyDATransactionsAggregates.total_transaction_fee_on_l1,
#             )
#             .filter(
#                 DailyDATransactionsAggregates.block_date <= datetime(2023, 12, 15),
#             )
#             .order_by(DailyDATransactionsAggregates.block_date.desc())
#         )
#
#         latest_celestia_da_fee_query = (
#             db.session.query(
#                 DailyCelestiaDaTransactionsAggregates.data_size,
#                 DailyCelestiaDaTransactionsAggregates.total_transaction_fee_on_celestia,
#             )
#             .filter(
#                 DailyCelestiaDaTransactionsAggregates.block_date > datetime(2023, 12, 15),
#             )
#             .order_by(DailyCelestiaDaTransactionsAggregates.block_date.desc())
#         )
#
#         latest_record = latest_da_fee_query.first()
#         latest_l1_da_fee = latest_record.total_transaction_fee_on_l1 if latest_record else 0
#
#         latest_celestia_record = latest_celestia_da_fee_query.first()
#         latest_celestia_da_fee = (
#             latest_celestia_record.total_transaction_fee_on_celestia if latest_celestia_record else 0
#         )
#         latest_data_size = latest_celestia_record.data_size if latest_celestia_record else 0
#
#         # Calculate DA Fee
#         # Fetches the latest and total transaction counts
#         transaction_count_query = (
#             db.session.query(
#                 DailyTransactionsAggregates.cnt.label("latest_transaction_cnt"),
#             )
#             .order_by(DailyTransactionsAggregates.block_date.desc())
#             .first()
#         )
#
#         latest_transaction_cnt = transaction_count_query.latest_transaction_cnt if transaction_count_query else 0
#
#         # Fetches the latest eth, tia price
#
#         eth_price = (
#             db.session.query(TokenHourlyPrices)
#             .filter(TokenHourlyPrices.symbol == "ETH")
#             .order_by(TokenHourlyPrices.timestamp.desc())
#             .first()
#         )
#
#         tia_price = (
#             db.session.query(TokenHourlyPrices)
#             .filter(TokenHourlyPrices.symbol == "TIA")
#             .order_by(TokenHourlyPrices.timestamp.desc())
#             .first()
#         )
#
#         # Calculate DA Fee
#         estimate_data_size = estimate_data_size_on_l1[transaction_type] * transaction_count
#         estimate_l1_da_fee_usd = round(
#             float(((latest_l1_da_fee / latest_transaction_cnt * transaction_count) / 10 ** 18 * eth_price.price))
#             * transaction_size_factors[transaction_type],
#             2,
#         )
#         estimate_celestia_da_fee_usd = float(
#             round(
#                 (
#                     (
#                             float(latest_celestia_da_fee)
#                             / float(latest_data_size)
#                             * float(estimate_data_size)
#                             * float(tia_price.price)
#                             / 1000000
#                     )
#                 ),
#                 2,
#             )
#         )
#
#         return {
#             "transaction_count": transaction_count,
#             "estimate_data_size": estimate_data_size,
#             "estimate_l1_da_fee_usd": estimate_l1_da_fee_usd,
#             "estimate_celestia_da_fee_usd": estimate_celestia_da_fee_usd,
#             "latest_hour_avg_eth_price": float(eth_price.price),
#             "latest_hour_avg_tia_price": float(tia_price.price),
#         }, 200


def limit_address(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Error! Invalid contract address format, the value must be a string.")

    if len(value) != 42:
        raise ValueError("Error! Invalid contract address format, the value must be 42 characters long.")

    if not value.startswith("0x"):
        raise ValueError("Error! Invalid contract address format, The value must start with '0x'.")

    if not all(c in "0123456789abcdefABCDEF" for c in value[2:]):
        raise ValueError(
            "Error! Invalid contract address format, The address must contain only hexadecimal characters."
        )

    return value


parser = reqparse.RequestParser()
parser.add_argument(
    "startblock",
    type=int,
    default=0,
    help="The integer block number to start searching for transactions",
)
parser.add_argument(
    "endblock",
    type=int,
    default=4999,
    help="The integer block number to stop searching for transactions",
)

parser.add_argument(
    "startdate",
    type=lambda x: datetime.strptime(x, "%Y-%m-%d"),
    required=False,
    help="Start date in YYYY-MM-DD format",
)
parser.add_argument(
    "enddate",
    type=lambda x: datetime.strptime(x, "%Y-%m-%d"),
    required=False,
    help="End date in YYYY-MM-DD format",
)

parser.add_argument("filtertype", choices=("date", "block"), default=None)
parser.add_argument("address", type=lambda x: limit_address(x), default=None)
parser.add_argument("contractaddress", type=lambda x: limit_address(x), default=None)


def get_block_number_range():
    args = parser.parse_args()
    filter_type = args.get("filtertype")
    if filter_type == "date":
        start_date = args.get("startdate")
        end_date = args.get("enddate")
        if not start_date or not end_date:
            raise APIError("Error date", code=400)

        start_timestamp = datetime.utcfromtimestamp(datetime.combine(start_date, time.min).timestamp())
        end_timestamp = datetime.utcfromtimestamp(datetime.combine(end_date, time.max).timestamp())

        start_block = Blocks.query.filter(Blocks.timestamp >= start_timestamp).order_by(Blocks.timestamp.asc()).first()
        end_block = Blocks.query.filter(Blocks.timestamp <= end_timestamp).order_by(Blocks.timestamp.desc()).first()

        start_block_number = start_block.number if start_block else 0
        end_block_number = end_block.number if end_block else 0

    else:
        start_block_number = args.get("startblock")
        end_block_number = args.get("endblock")
    return start_block_number, end_block_number


def response_csv(data, filename, header):
    si = io.StringIO()
    cw = csv.DictWriter(si, fieldnames=header)

    if header:
        cw.writeheader()

    cw.writerows(data)
    output = Response(si.getvalue(), mimetype="text/csv")
    output.headers["Content-Disposition"] = "attachment; filename={}.csv".format(filename)
    output.headers["Content-type"] = "text/csv; charset=utf-8"

    return output


@explorer_namespace.route("/v1/explorer/export/transactions/<address>")
class ExplorerExportTransactions(Resource):
    def get(self, address):
        if not address or is_eth_address(address) is False:
            raise APIError("Error Wallet Address", code=400)
        address = address.lower()
        address_bytes = bytes.fromhex(address[2:])

        start_block_number, end_block_number = get_block_number_range()

        transactions = (
            db.session.query(Transactions)
            .filter(
                and_(
                    Transactions.block_number >= start_block_number,
                    Transactions.block_number <= end_block_number,
                    or_(
                        Transactions.from_address == address_bytes,
                        Transactions.to_address == address_bytes,
                    ),
                )
            )
            .order_by(
                Transactions.block_number.asc(),
                Transactions.transaction_index.asc(),
            )
            .limit(5000)
        )
        header = [
            "blockNumber",
            "timeStamp",
            "hash",
            "nonce",
            "blockHash",
            "transactionIndex",
            "from",
            "to",
            "value",
            "gas",
            "gasPrice",
            "isError",
            "receiptStatus",
            "contractAddress",
            "cumulativeGasUsed",
            "gasUsed",
            "methodId",
        ]
        result = [
            {
                "blockNumber": str(transaction.block_number),
                "timeStamp": transaction.block_timestamp.strftime("%s"),
                "hash": '0x' + transaction.hash.hex(),
                "nonce": str(transaction.nonce),
                "blockHash": '0x' + transaction.block_hash.hex(),
                "transactionIndex": str(transaction.transaction_index),
                "from": '0x' + transaction.from_address.hex(),
                "to": '0x' + transaction.to_address.hex(),
                "value": str(transaction.value),
                "gas": str(transaction.gas),
                "gasPrice": str(transaction.gas_price),
                "isError": "0" if transaction.receipt_status == 1 else "1",
                "receiptStatus": str(transaction.receipt_status),
                "contractAddress": transaction.receipt_contract_address,
                "cumulativeGasUsed": str(transaction.receipt_cumulative_gas_used),
                "gasUsed": str(transaction.receipt_gas_used),
                "methodId": '0x' + transaction.input.hex()[0:10],
            }
            for transaction in transactions
        ]
        return response_csv(
            result,
            "transactions-{}-{}".format(address, datetime.now().strftime("%Y%m%d%H%M%S")),
            header,
        )


@explorer_namespace.route("/v1/explorer/export/internal_transactions/<address>")
class ExplorerExportInternalTransactions(Resource):
    def get(self, address):
        if not address or is_eth_address(address) is False:
            raise APIError("Error Wallet Address", code=400)
        address = address.lower()
        address_bytes = bytes.fromhex(address[2:])

        start_block_number, end_block_number = get_block_number_range()

        internal_transactions = (
            db.session.query(ContractInternalTransactions)
            .filter(
                and_(
                    ContractInternalTransactions.block_number >= start_block_number,
                    ContractInternalTransactions.block_number <= end_block_number,
                    or_(
                        ContractInternalTransactions.from_address == address_bytes,
                        ContractInternalTransactions.to_address == address_bytes,
                    ),
                )
            )
            .order_by(
                ContractInternalTransactions.block_number.asc(),
                ContractInternalTransactions.transaction_index.asc(),
            )
            .limit(5000)
        )
        header = [
            "blockNumber",
            "timeStamp",
            "hash",
            "from",
            "to",
            "value",
            "contractAddress",
            "type",
            "gas",
            "traceId",
            "isError",
            "errCode",
        ]
        result = [
            {
                "blockNumber": str(internal_transaction.block_number),
                "timeStamp": internal_transaction.block_timestamp.strftime("%s"),
                "hash": '0x' + internal_transaction.transaction_hash.hex(),
                "from": '0x' + internal_transaction.from_address.hex(),
                "to": '0x' + internal_transaction.to_address.hex(),
                "value": str(internal_transaction.value),
                "contractAddress": (
                    '0x' + internal_transaction.to_address.hex()
                    if internal_transaction.trace_type in ["create", "create2"] else ""
                ),
                "type": internal_transaction.trace_type,
                "gas": str(internal_transaction.gas),
                "traceId": internal_transaction.trace_id,
                "isError": "1" if internal_transaction.error == 0 else "0",
                "errCode": internal_transaction.error,
            }
            for internal_transaction in internal_transactions
        ]
        return response_csv(
            result,
            "transactions-{}-{}".format(address, datetime.now().strftime("%Y%m%d%H%M%S")),
            header,
        )


token_relationships = {
    "ERC20": {
        "TokenTable": Tokens,
        "TokenTransferTable": ERC20TokenTransfers,
        "TokenHoldersTable": ERC20TokenHolders,
    },
    "ERC721": {
        "TokenTable": Tokens,
        "TokenTransferTable": ERC721TokenTransfers,
        "TokenHoldersTable": ERC721TokenHolders,
    },
    "ERC1155": {
        "TokenTable": Tokens,
        "TokenTransferTable": ERC1155TokenTransfers,
        "TokenHoldersTable": ERC1155TokenHolders,
    },
}


def token_transfers(contract_address, address, start_block_number, end_block_number, token_type):
    TokenTable = token_relationships[token_type]["TokenTable"]
    TokenTransferTable = token_relationships[token_type]["TokenTransferTable"]
    condition = True
    if contract_address:
        contract_address = contract_address.lower()
        contract_address_bytes = bytes.fromhex(contract_address[2:])

        condition = and_(condition, TokenTransferTable.token_address == contract_address_bytes)
    if address:
        address = address.lower()
        address_bytes = bytes.fromhex(address[2:])

        condition = and_(
            condition,
            or_(
                TokenTransferTable.from_address == address_bytes,
                TokenTransferTable.to_address == address_bytes,
            ),
        )
    if address is None and contract_address is None:
        raise APIError("Error address", code=400)

    transfers = (
        TokenTransferTable.query.filter(
            and_(
                condition,
                TokenTransferTable.block_number >= start_block_number,
                TokenTransferTable.block_number <= end_block_number,
            )
        )
        .join(
            Transactions,
            TokenTransferTable.transaction_hash == Transactions.hash,
        )
        .add_columns(
            Transactions.nonce,
            Transactions.gas,
            Transactions.gas_price,
            Transactions.receipt_gas_used,
            Transactions.receipt_cumulative_gas_used,
            Transactions.transaction_index,
            Transactions.input,
        )
        .order_by(TokenTransferTable.block_number.asc())
        .limit(5000)
    )

    token_addresses = set([transfer.token_address for transfer, _, _, _, _, _, _, _ in transfers])

    tokens = TokenTable.query.filter(TokenTable.address.in_(token_addresses)).all()
    token_dict = {token.address: token for token in tokens}

    result = []
    for (
            transfer,
            nonce,
            gas,
            gas_price,
            receipt_gas_used,
            receipt_cumulative_gas_used,
            transaction_index,
            input,
    ) in transfers:
        transfer_data = {
            "blockNumber": str(transfer.block_number),
            "timeStamp": transfer.block_timestamp.strftime("%s"),
            "hash": '0x' + transfer.transaction_hash.hex(),
            "nonce": str(nonce),
            "blockHash": '0x' + transfer.block_hash.hex(),
            "contractAddress": '0x' + transfer.token_address.hex(),
            "from": '0x' + transfer.from_address.hex(),
            "to": '0x' + transfer.to_address.hex(),
            "tokenName": token_dict.get(transfer.token_address).name,
            "tokenSymbol": token_dict.get(transfer.token_address).symbol,
            "transactionIndex": str(transaction_index),
            "gas": str(gas),
            "gasPrice": str(gas_price),
            "gasUsed": str(receipt_gas_used),
            "cumulativeGasUsed": str(receipt_cumulative_gas_used),
            # 'input': 'deprecated', // TODO
            # 'confirmations': str(transaction.confirmations), // TODO
        }
        if token_type == "ERC20":
            transfer_data["value"] = str(transfer.value)
            transfer_data["tokenDecimal"] = str(token_dict.get(transfer.token_address).decimals)
        elif token_type == "ERC721":
            transfer_data["tokenID"] = str(transfer.token_id)
        elif token_type == "ERC1155":
            transfer_data["tokenValue"] = str(transfer.value)
            transfer_data["tokenID"] = str(transfer.token_id)

        result.append(transfer_data)
    return result


def token_holder_list(contract_address, token_type):
    contract_address = contract_address.lower()
    contract_address_bytes = bytes.fromhex(contract_address[2:])

    TokenTable = token_relationships[token_type]["TokenTable"]
    TokenHoldersTable = token_relationships[token_type]["TokenHoldersTable"]

    token = TokenTable.query.filter_by(address=contract_address_bytes).first()
    if token is None:
        return []

    token_holders = (
        TokenHoldersTable.query.with_entities(
            TokenHoldersTable.wallet_address,
            func.sum(TokenHoldersTable.balance_of).label("balance_of"),
        )
        .filter_by(token_address=contract_address_bytes)
        .filter(TokenHoldersTable.balance_of > 0)
        .group_by(TokenHoldersTable.wallet_address)
        .order_by(func.sum(TokenHoldersTable.balance_of).desc())
        .limit(10000)
    )
    result = [
        {
            "TokenHolderAddress": token_holder.wallet_address,
            "TokenHolderQuantity": str(token_holder.balance_of),
        }
        for token_holder in token_holders
    ]

    return result


@explorer_namespace.route("/v1/explorer/export/token_transfers")
class ExplorerExportTokenTransfer(Resource):
    def get(self):
        start_block_number, end_block_number = get_block_number_range()
        args = parser.parse_args()
        header = [
            "blockNumber",
            "timeStamp",
            "hash",
            "nonce",
            "blockHash",
            "contractAddress",
            "from",
            "to",
            "tokenName",
            "tokenSymbol",
            "transactionIndex",
            "gas",
            "gasPrice",
            "gasUsed",
            "cumulativeGasUsed",
            "value",
            "tokenDecimal",
        ]
        result = token_transfers(
            args.get("contractaddress"),
            args.get("address"),
            start_block_number,
            end_block_number,
            "ERC20",
        )

        return response_csv(
            result,
            "erc20_token_transfers-{}".format(datetime.now().strftime("%Y%m%d%H%M%S")),
            header,
        )


@explorer_namespace.route("/v1/explorer/export/nft_token_transfers")
class ExplorerExportNFTTokenTransfer(Resource):
    def get(self):
        start_block_number, end_block_number = get_block_number_range()
        args = parser.parse_args()
        header = [
            "blockNumber",
            "timeStamp",
            "hash",
            "nonce",
            "blockHash",
            "contractAddress",
            "from",
            "to",
            "tokenName",
            "tokenSymbol",
            "transactionIndex",
            "gas",
            "gasPrice",
            "gasUsed",
            "cumulativeGasUsed",
            "tokenID",
        ]

        result = token_transfers(
            args.get("contractaddress"),
            args.get("address"),
            start_block_number,
            end_block_number,
            "ERC721",
        )
        return response_csv(
            result,
            "erc721_token_transfers-{}".format(datetime.now().strftime("%Y%m%d%H%M%S")),
            header,
        )


@explorer_namespace.route("/v1/explorer/export/nft1155_token_transfers")
class ExplorerExportNFT1155TokenTransfer(Resource):
    def get(self):
        start_block_number, end_block_number = get_block_number_range()
        args = parser.parse_args()
        header = [
            "blockNumber",
            "timeStamp",
            "hash",
            "nonce",
            "blockHash",
            "contractAddress",
            "from",
            "to",
            "tokenName",
            "tokenSymbol",
            "transactionIndex",
            "gas",
            "gasPrice",
            "gasUsed",
            "cumulativeGasUsed",
            "tokenValue",
            "tokenID",
        ]

        result = token_transfers(
            args.get("contractaddress"),
            args.get("address"),
            start_block_number,
            end_block_number,
            "ERC1155",
        )
        return response_csv(
            result,
            "erc1155_token_transfers-{}".format(datetime.now().strftime("%Y%m%d%H%M%S")),
            header,
        )


@explorer_namespace.route("/v1/explorer/export/token_holders/<contract_address>")
class ExplorerExportTokenHolders(Resource):
    def get(self, contract_address):
        if not contract_address or (contract_address and len(contract_address) != 42):
            raise APIError("Error Wallet Address", code=400)
        header = ["TokenHolderAddress", "TokenHolderQuantity"]
        result = token_holder_list(contract_address, "ERC20")
        return response_csv(
            result,
            "erc20_token_holders-{}".format(datetime.now().strftime("%Y%m%d%H%M%S")),
            header,
        )


@explorer_namespace.route("/v1/explorer/export/nft_token_holders/<contract_address>")
class ExplorerExportNFTTokenHolders(Resource):
    def get(self, contract_address):
        if not contract_address or (contract_address and len(contract_address) != 42):
            raise APIError("Error Wallet Address", code=400)
        header = ["TokenHolderAddress", "TokenHolderQuantity"]
        result = token_holder_list(contract_address, "ERC721")
        return response_csv(
            result,
            "erc721_token_holders-{}".format(datetime.now().strftime("%Y%m%d%H%M%S")),
            header,
        )


@explorer_namespace.route("/v1/explorer/export/nft1155_token_holders/<contract_address>")
class ExplorerExportNFT1155TokenHolders(Resource):
    def get(self, contract_address):
        if not contract_address or (contract_address and len(contract_address) != 42):
            raise APIError("Error Wallet Address", code=400)
        header = ["TokenHolderAddress", "TokenHolderQuantity"]
        result = token_holder_list(contract_address, "ERC1155")
        return response_csv(
            result,
            "erc1155_token_holders-{}".format(datetime.now().strftime("%Y%m%d%H%M%S")),
            header,
        )
