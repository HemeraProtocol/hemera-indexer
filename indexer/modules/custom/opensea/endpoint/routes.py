from datetime import datetime
from typing import Any, Dict, List, Union

from flask import request
from flask_restx import Resource
from sqlalchemy import and_, desc, func

from api.app.cache import cache
from api.app.token.token_prices import TokenHourlyPrices
from common.models import db
from common.models.tokens import Tokens
from common.utils.exception_control import APIError
from common.utils.format_utils import as_dict, format_to_dict
from indexer.modules.custom.opensea.endpoint import opensea_namespace
from indexer.modules.custom.opensea.models.address_opensea_profile import AddressOpenseaProfile
from indexer.modules.custom.opensea.models.address_opensea_transaction import AddressOpenseaTransactions
from indexer.modules.custom.opensea.models.opensea_crypto_mapping import OpenseaCryptoTokenMapping
from indexer.modules.custom.opensea.models.opensea_order import OpenseaOrders
from indexer.modules.custom.opensea.models.scheduled_metadata import ScheduledMetadata
from indexer.modules.custom.opensea.opensea_job import get_item_type_string

PAGE_SIZE = 10
MAX_TRANSACTION = 500000
MAX_TRANSACTION_WITH_CONDITION = 10000
MAX_INTERNAL_TRANSACTION = 10000
MAX_TOKEN_TRANSFER = 10000


def get_opensea_profile_by_address(address: Union[str, bytes]):
    if isinstance(address, str):
        address = bytes.fromhex(address[2:])
    opensea_profile = db.session().query(AddressOpenseaProfile).filter_by(address=address).first()
    if not opensea_profile:
        raise APIError("The address has no opensea transaction", code=400)
    return opensea_profile


def get_opensea_order_count_by_address(address: Union[str, bytes]):
    if isinstance(address, str):
        address = bytes.fromhex(address[2:])
    result = (
        db.session.query(AddressOpenseaProfile)
        .with_entities(AddressOpenseaProfile.opensea_order_count)
        .filter(AddressOpenseaProfile.address == address)
        .first()
    )
    return result


def get_opensea_address_order_cnt(address: Union[str, bytes]):
    if isinstance(address, str):
        address = bytes.fromhex(address[2:])
    last_timestamp = db.session.query(func.max(ScheduledMetadata.last_data_timestamp)).scalar()
    recently_txn_count = (
        db.session.query(AddressOpenseaTransactions.address)
        .filter(
            and_(
                AddressOpenseaTransactions.address == address,
                (
                    AddressOpenseaTransactions.block_timestamp >= last_timestamp.date()
                    if last_timestamp is not None
                    else True
                ),
            ),
        )
        .count()
    )
    result = get_opensea_order_count_by_address(address)
    past_txn_count = 0 if not result else result[0]
    total_count = past_txn_count + recently_txn_count
    return total_count


def get_token_price(token_address: str, timestamp: datetime) -> float:
    if token_address == "0x0000000000000000000000000000000000000000":
        # For ETH, get the price from TokenHourlyPrices
        price_record = (
            db.session.query(TokenHourlyPrices)
            .filter(TokenHourlyPrices.symbol == "ETH")
            .filter(TokenHourlyPrices.timestamp <= timestamp)
            .order_by(desc(TokenHourlyPrices.timestamp))
            .first()
        )
        return float(price_record.price) if price_record else 0
    else:
        # For other tokens, get the price symbol from the mapping table
        mapping = (
            db.session.query(OpenseaCryptoTokenMapping)
            .filter(OpenseaCryptoTokenMapping.address_var == token_address)
            .first()
        )
        if mapping and mapping.price_symbol:
            price_record = (
                db.session.query(TokenHourlyPrices)
                .filter(TokenHourlyPrices.symbol == mapping.price_symbol)
                .filter(TokenHourlyPrices.timestamp <= timestamp)
                .order_by(desc(TokenHourlyPrices.timestamp))
                .first()
            )
            return float(price_record.price) if price_record else 0
    return 0


def calculate_usd_value(amount: float, token_address: str, timestamp: datetime) -> float:
    price = get_token_price(token_address, timestamp)
    return amount * price


def parse_item(item: Dict[str, Any], token_info: Dict[str, Any], timestamp: datetime) -> Dict[str, Any]:
    parsed_item = {
        "token_address": item["token"],
        "token_name": token_info.get(item["token"], {}).get("name"),
        "token_type": get_item_type_string(item["itemType"]),
        "token_symbol": token_info.get(item["token"], {}).get("symbol"),
        "amount": (
            int(item["amount"])
            if item["itemType"] >= 2
            else float(item["amount"]) / (10 ** token_info.get(item["token"], {}).get("decimals", 18))
        ),
        "identifier": int(item["identifier"]) if item["identifier"] else None,
    }
    if item["itemType"] < 2:
        parsed_item["usd_value"] = calculate_usd_value(parsed_item["amount"], item["token"], timestamp)
    return parsed_item


def fetch_token_info(token_addresses: List[str]) -> Dict[str, Any]:
    byte_addresses = [bytes.fromhex(addr[2:]) for addr in token_addresses]
    token_infos = db.session.query(Tokens).filter(Tokens.address.in_(byte_addresses)).all()
    return {"0x" + token.address.hex(): as_dict(token) for token in token_infos}


def parse_opensea_order(order: OpenseaOrders, token_info: Dict[str, Any]) -> Dict[str, Any]:
    parsed_order = {
        "order_hash": order.order_hash,
        "offer": [parse_item(item, token_info, order.block_timestamp) for item in order.offer],
        "consideration": [parse_item(item, token_info, order.block_timestamp) for item in order.consideration],
        "transaction_hash": order.transaction_hash,
        "block_timestamp": order.block_timestamp,
        "block_number": order.block_number,
        "zone": order.zone,
        "protocol_version": order.protocol_version,
    }
    return parsed_order


def format_opensea_transaction(transaction: Dict[str, Any]) -> Dict[str, Any]:
    formatted_transaction = {
        "address": transaction["address"],
        "transaction_hash": transaction["transaction_hash"],
        "block_number": transaction["block_number"],
        "block_timestamp": transaction["block_timestamp"],
        "order_hash": transaction["order_hash"],
        "protocol_version": transaction["protocol_version"],
        "zone": transaction["zone"],
        "transaction_type": "buy" if not transaction["is_offer"] else "sell",
    }

    # Calculate volume and determine items
    if not transaction["is_offer"]:  # Buy transaction
        volume = sum(item.get("usd_value", 0) for item in transaction["consideration"])
        items = transaction["offer"]
    else:  # Sell transaction
        volume = sum(item.get("usd_value", 0) for item in transaction["offer"])
        items = transaction["consideration"]

    formatted_transaction["volume_usd"] = volume

    formatted_items = []
    for item in items:
        formatted_item = {
            "token_address": item["token_address"],
            "token_name": item["token_name"],
            "token_type": item["token_type"],
            "token_symbol": item["token_symbol"],
            "amount": item["amount"],
            "identifier": item["identifier"],
        }
        formatted_items.append(formatted_item)

    formatted_transaction["items"] = formatted_items

    return formatted_transaction


def parse_opensea_order_transactions(transactions: List[AddressOpenseaTransactions]) -> List[Dict[str, Any]]:
    order_hashes = [transaction.order_hash for transaction in transactions]
    orders = db.session.query(OpenseaOrders).filter(OpenseaOrders.order_hash.in_(order_hashes)).all()

    token_addresses = set()
    for order in orders:
        for item in order.offer + order.consideration:
            token_addresses.add(item["token"])

    token_info = fetch_token_info(list(token_addresses))
    order_dict = {}
    for order in orders:
        order_dict["0x" + order.order_hash.hex()] = parse_opensea_order(order, token_info)

    parsed_transactions = []
    for transaction in transactions:
        transaction_dict = format_to_dict(as_dict(transaction) | order_dict.get("0x" + transaction.order_hash.hex()))

        parsed_transactions.append(format_opensea_transaction(transaction_dict))

    return parsed_transactions


def get_opensea_transactions_by_address(address, limit=1, offset=0):
    if isinstance(address, str):
        address = bytes.fromhex(address[2:])
    transactions = (
        db.session.query(AddressOpenseaTransactions)
        .order_by(
            AddressOpenseaTransactions.block_number.desc(),
            AddressOpenseaTransactions.log_index.desc(),
        )
        .filter(AddressOpenseaTransactions.address == address)
        .limit(limit)
        .offset(offset)
        .all()
    )
    return transactions


def get_latest_opensea_transaction_by_address(address: Union[str, bytes]):
    if isinstance(address, str):
        address = bytes.fromhex(address[2:])
    last_opensea_transaction = (
        db.session()
        .query(AddressOpenseaTransactions)
        .filter_by(address=address)
        .order_by(desc(AddressOpenseaTransactions.block_number), desc(AddressOpenseaTransactions.log_index))
        .first()
    )
    if not last_opensea_transaction:
        return {}
    return {
        "latest_transaction_hash": "0x" + last_opensea_transaction.transaction_hash.hex(),
        "latest_block_timestamp": last_opensea_transaction.block_timestamp.astimezone().isoformat("T", "seconds"),
    }


@opensea_namespace.route("/v1/explorer/custom/opensea/address/<address>/profile")
class ExplorerCustomOpenseaAddressProfile(Resource):
    @cache.cached(timeout=60)
    def get(self, address):
        address = address.lower()

        profile = get_opensea_profile_by_address(address)

        return as_dict(profile) | get_latest_opensea_transaction_by_address(address)


@opensea_namespace.route("/v1/explorer/custom/opensea/address/<address>/transactions")
class ExplorerCustomOpenseaAddressTransactions(Resource):
    @cache.cached(timeout=10)
    def get(self, address):
        address = address.lower()
        page_index = int(request.args.get("page", 1))
        page_size = int(request.args.get("size", PAGE_SIZE))

        opensea_transactions = get_opensea_transactions_by_address(
            address,
            limit=page_size,
            offset=(page_index - 1) * page_size,
        )

        if len(opensea_transactions) < page_size:
            total_count = len(opensea_transactions)
        else:
            total_count = get_opensea_address_order_cnt(address)

        transaction_list = parse_opensea_order_transactions(opensea_transactions)

        return {
            "data": transaction_list,
            "total": total_count,
        }, 200
