import binascii
import re
from operator import or_

from api.app.cache import cache
from api.app.l2_explorer import l2_explorer_namespace
from common.models import db as postgres_db
from common.models.bridge import BridgeTokens, L1ToL2BridgeTransactions, L2ToL1BridgeTransactions, OpBedrockStateBatches
from common.models.tokens import Tokens
from common.utils.bridge_utils import BridgeTransactionParser
from common.utils.config import get_config
from common.utils.exception_control import APIError
from common.utils.format_utils import format_to_dict
from common.utils.web3_utils import is_eth_address
from flask import request
from flask_restx import Resource
from sqlalchemy import and_, func

app_config = get_config()

PAGE_SIZE = 25
MAX_TRANSACTION = 500000
MAX_TRANSACTION_WITH_CONDITION = 10000
MAX_INTERNAL_TRANSACTION = 10000
MAX_TOKEN_TRANSFER = 10000

bridge_transaction_parser = BridgeTransactionParser.init_from_config(get_config())


def get_deposit_count_by_address(address):
    address_bin = binascii.unhexlify(address[2:])
    recently_txn_count = (
        postgres_db.session.query(L1ToL2BridgeTransactions.l1_transaction_hash)
        .filter(
            and_(
                L1ToL2BridgeTransactions.to_address == address_bin,
            )
        )
        .count()
    )
    total_count = recently_txn_count
    return total_count


def get_withdraw_count_by_address(address):
    address_bin = binascii.unhexlify(address[2:])
    recently_txn_count = (
        postgres_db.session.query(L2ToL1BridgeTransactions.l2_transaction_hash)
        .filter(
            L2ToL1BridgeTransactions.from_address == address_bin,
        )
        .count()
    )
    total_count = recently_txn_count
    return total_count


@l2_explorer_namespace.route("/v2/explorer/l1_to_l2_transactions")
@l2_explorer_namespace.route("/v1/explorer/l1_to_l2_transactions")
class ExplorerL1ToL2BridgeTransactions(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self):
        page_index = int(request.args.get("page", 1))
        page_size = int(request.args.get("size", PAGE_SIZE))
        address = request.args.get("address", None)
        type = request.args.get("type", None)
        token_address = request.args.get("token_address", None)

        if page_index <= 0 or page_size <= 0:
            return {"error": "Invalid page or size"}, 400

        if address and is_eth_address(address) is False:
            return {"error": "Invalid wallet address"}, 400

        if page_index * page_size > MAX_INTERNAL_TRANSACTION:
            return {"error": f"Showing the last {MAX_INTERNAL_TRANSACTION} records only"}, 400

        query = postgres_db.session.query(L1ToL2BridgeTransactions).filter(
            L1ToL2BridgeTransactions.l1_block_number != None
        )

        if type is not None and type.isdigit():
            query = query.filter(L1ToL2BridgeTransactions._type == int(type))

        if address:
            address_bin = binascii.unhexlify(address[2:])
            query = query.filter(L1ToL2BridgeTransactions.to_address == address_bin)

        if app_config.chain in ["taiko"] or app_config.l2_config.rollup_type == "arbitrum":
            query = query.outerjoin(
                BridgeTokens,
                or_(
                    L1ToL2BridgeTransactions.l1_token_address == BridgeTokens.l1_token_address,
                    L1ToL2BridgeTransactions.l2_token_address == BridgeTokens.l2_token_address,
                ),
            ).with_entities(
                L1ToL2BridgeTransactions.l1_block_number,
                L1ToL2BridgeTransactions.l1_block_timestamp,
                L1ToL2BridgeTransactions.l1_transaction_hash,
                L1ToL2BridgeTransactions.l2_block_number,
                L1ToL2BridgeTransactions.l2_block_timestamp,
                L1ToL2BridgeTransactions.l2_transaction_hash,
                L1ToL2BridgeTransactions.amount,
                L1ToL2BridgeTransactions.from_address,
                L1ToL2BridgeTransactions.to_address,
                func.coalesce(
                    BridgeTokens.l1_token_address,
                    L1ToL2BridgeTransactions.l1_token_address,
                ).label("l1_token_address"),
                func.coalesce(
                    BridgeTokens.l2_token_address,
                    L1ToL2BridgeTransactions.l2_token_address,
                ).label("l2_token_address"),
                L1ToL2BridgeTransactions.extra_info,
                L1ToL2BridgeTransactions._type,
                L1ToL2BridgeTransactions.index,
                L1ToL2BridgeTransactions.l1_block_hash,
                L1ToL2BridgeTransactions.l2_block_hash,
                L1ToL2BridgeTransactions.l1_from_address,
                L1ToL2BridgeTransactions.l2_from_address,
            )
        else:
            query = query.with_entities(
                L1ToL2BridgeTransactions.l1_block_number,
                L1ToL2BridgeTransactions.l1_block_timestamp,
                L1ToL2BridgeTransactions.l1_transaction_hash,
                L1ToL2BridgeTransactions.l2_block_number,
                L1ToL2BridgeTransactions.l2_block_timestamp,
                L1ToL2BridgeTransactions.l2_transaction_hash,
                L1ToL2BridgeTransactions.amount,
                L1ToL2BridgeTransactions.from_address,
                L1ToL2BridgeTransactions.to_address,
                L1ToL2BridgeTransactions.l1_token_address,
                L1ToL2BridgeTransactions.l2_token_address,
                L1ToL2BridgeTransactions.extra_info,
                L1ToL2BridgeTransactions._type,
                L1ToL2BridgeTransactions.index,
                L1ToL2BridgeTransactions.l1_block_hash,
                L1ToL2BridgeTransactions.l2_block_hash,
                L1ToL2BridgeTransactions.l1_from_address,
                L1ToL2BridgeTransactions.l2_from_address,
            )

        if token_address:
            if not re.match(r"^0x[a-fA-F0-9]{40}$", token_address):
                raise APIError("Invalid wallet address", code=400)
            if token_address.lower() == "0xdeaddeaddeaddeaddeaddeaddeaddeaddead1111":
                query = query.filter(L1ToL2BridgeTransactions.l2_token_address == None)
            else:
                token_address_bin = binascii.unhexlify(token_address[2:])
                query = query.filter(L1ToL2BridgeTransactions.l2_token_address == token_address_bin)

        transactions = (
            query.order_by(L1ToL2BridgeTransactions.l1_block_number.desc())
            .limit(page_size)
            .offset((page_index - 1) * page_size)
            .all()
        )

        token_addresses = {transaction.l2_token_address for transaction in transactions}
        tokens = postgres_db.session.query(Tokens).filter(Tokens.address.in_(token_addresses)).all()
        bridge_transaction_parser.complete_format_tokens(tokens)
        token_info_dict = {token.address: token for token in tokens}

        transaction_list = []
        for transaction in transactions:
            transaction_list.append(
                bridge_transaction_parser.parse_bridge_l1_to_l2_transaction(
                    format_to_dict(transaction),
                    format_to_dict(token_info_dict.get(transaction.l2_token_address)),
                )
            )
        if token_address is None and address is None and type is None:
            total_records = L1ToL2BridgeTransactions.query.count()
        elif token_address is None and address and type is not None:
            total_records = get_deposit_count_by_address(address)
        else:
            total_records = query.count()

        response = {
            "data": transaction_list,
            "total": total_records,
            "max_display": min(total_records, MAX_INTERNAL_TRANSACTION),
            "page": page_index,
            "size": page_size,
        }
        return response, 200


@l2_explorer_namespace.route("/v2/explorer/l2_to_l1_transactions")
@l2_explorer_namespace.route("/v1/explorer/l2_to_l1_transactions")
class ExplorerL2oL1Transactions(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self):
        page_index = int(request.args.get("page", 1))
        page_size = int(request.args.get("size", PAGE_SIZE))
        address = request.args.get("address", None)
        type = request.args.get("type", None)
        token_address = request.args.get("token_address", None)

        if page_index <= 0 or page_size <= 0:
            return {"error": "Invalid page or size"}, 400

        if page_index * page_size > MAX_INTERNAL_TRANSACTION:
            return {"error": f"Showing the last {MAX_INTERNAL_TRANSACTION} records only"}, 400

        query = postgres_db.session.query(L2ToL1BridgeTransactions).filter(
            L2ToL1BridgeTransactions.l2_block_number != None
        )

        if address:
            address_bin = binascii.unhexlify(address[2:])
            query = query.filter(L2ToL1BridgeTransactions.to_address == address_bin)
        if app_config.chain == "taiko" or app_config.chain == "arbitrum":
            query = query.outerjoin(
                BridgeTokens,
                or_(
                    L2ToL1BridgeTransactions.l1_token_address == BridgeTokens.l1_token_address,
                    L2ToL1BridgeTransactions.l2_token_address == BridgeTokens.l2_token_address,
                ),
            ).with_entities(
                L2ToL1BridgeTransactions.l1_block_number,
                L2ToL1BridgeTransactions.l1_block_timestamp,
                L2ToL1BridgeTransactions.l1_transaction_hash,
                L2ToL1BridgeTransactions.l2_block_number,
                L2ToL1BridgeTransactions.l2_block_timestamp,
                L2ToL1BridgeTransactions.l2_transaction_hash,
                L2ToL1BridgeTransactions.amount,
                L2ToL1BridgeTransactions.from_address,
                L2ToL1BridgeTransactions.to_address,
                func.coalesce(
                    BridgeTokens.l1_token_address,
                    L2ToL1BridgeTransactions.l1_token_address,
                ).label("l1_token_address"),
                func.coalesce(
                    BridgeTokens.l2_token_address,
                    L2ToL1BridgeTransactions.l2_token_address,
                ).label("l2_token_address"),
                L2ToL1BridgeTransactions.extra_info,
                L2ToL1BridgeTransactions.l1_proven_transaction_hash,
                L2ToL1BridgeTransactions.l1_proven_block_number,
                L2ToL1BridgeTransactions.l1_proven_block_timestamp,
                L2ToL1BridgeTransactions._type,
                L2ToL1BridgeTransactions.index,
                L2ToL1BridgeTransactions.l1_block_hash,
                L2ToL1BridgeTransactions.l2_block_hash,
                L2ToL1BridgeTransactions.l1_from_address,
                L2ToL1BridgeTransactions.l2_from_address,
            )
        else:
            query = query.with_entities(
                L2ToL1BridgeTransactions.l1_block_number,
                L2ToL1BridgeTransactions.l1_block_timestamp,
                L2ToL1BridgeTransactions.l1_transaction_hash,
                L2ToL1BridgeTransactions.l2_block_number,
                L2ToL1BridgeTransactions.l2_block_timestamp,
                L2ToL1BridgeTransactions.l2_transaction_hash,
                L2ToL1BridgeTransactions.amount,
                L2ToL1BridgeTransactions.from_address,
                L2ToL1BridgeTransactions.to_address,
                L2ToL1BridgeTransactions.l1_token_address,
                L2ToL1BridgeTransactions.l2_token_address,
                L2ToL1BridgeTransactions.extra_info,
                L2ToL1BridgeTransactions.l1_proven_transaction_hash,
                L2ToL1BridgeTransactions.l1_proven_block_number,
                L2ToL1BridgeTransactions.l1_proven_block_timestamp,
                L2ToL1BridgeTransactions._type,
                L2ToL1BridgeTransactions.index,
                L2ToL1BridgeTransactions.l1_block_hash,
                L2ToL1BridgeTransactions.l2_block_hash,
                L2ToL1BridgeTransactions.l1_from_address,
                L2ToL1BridgeTransactions.l2_from_address,
            )

        if token_address:
            if not re.match(r"^0x[a-fA-F0-9]{40}$", token_address):
                raise APIError("Invalid wallet address", code=400)
            if token_address.lower() == "0xdeaddeaddeaddeaddeaddeaddeaddeaddead1111":
                query = query.filter(L2ToL1BridgeTransactions.l2_token_address == None)
            else:
                token_address_bin = binascii.unhexlify(token_address[2:])
                query = query.filter(L2ToL1BridgeTransactions.l2_token_address == token_address_bin)

        transactions = (
            query.order_by(L2ToL1BridgeTransactions.l2_block_number.desc())
            .limit(page_size)
            .offset((page_index - 1) * page_size)
            .all()
        )

        token_addresses = {transaction.l2_token_address for transaction in transactions}
        tokens = postgres_db.session.query(Tokens).filter(Tokens.address.in_(token_addresses)).all()
        bridge_transaction_parser.complete_format_tokens(tokens)
        token_info_dict = {token.address: token for token in tokens}

        transaction_list = []

        finalized_block_number = (
            postgres_db.session.query(OpBedrockStateBatches.end_block_number)
            .order_by(OpBedrockStateBatches.batch_index.desc())
            .first()
        )
        finalized_block_number = finalized_block_number[0] if finalized_block_number else None
        for transaction in transactions:
            transaction_list.append(
                bridge_transaction_parser.parse_bridge_l2_to_l1_transaction(
                    format_to_dict(transaction),
                    format_to_dict(token_info_dict.get(transaction.l2_token_address)),
                    finalized_block_number,
                )
            )

        if token_address is None and address is None and type is None:
            total_records = L2ToL1BridgeTransactions.query.count()
        elif token_address is None and address and type is not None:
            total_records = get_withdraw_count_by_address(address)
        else:
            total_records = query.count()
        response = {
            "data": transaction_list,
            "total": total_records,
            "max_display": min(total_records, MAX_INTERNAL_TRANSACTION),
            "page": page_index,
            "size": page_size,
        }
        return response, 200
