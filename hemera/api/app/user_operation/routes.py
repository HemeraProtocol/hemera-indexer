import re

import flask
from api.app.cache import cache
from api.app.utils.fill_info import fill_address_display_to_transactions, process_token_transfer
from api.app.utils.parse_utils import parse_log_with_transaction_input_list
from common.models.erc20_token_transfers import ERC20TokenTransfers
from common.models.erc721_token_transfers import ERC721TokenTransfers
from common.models.erc1155_token_transfers import ERC1155TokenTransfers
from common.models.logs import Logs
from common.models.tokens import Tokens
from common.models.transactions import Transactions
from common.utils.config import get_config
from common.utils.db_utils import get_total_row_count
from common.utils.exception_control import APIError
from common.utils.format_utils import format_value_for_json, hex_str_to_bytes
from flask_restx import Resource
from indexer.modules.user_ops.models.user_operation_results import UserOperationResult

from api.app.user_operation import user_operation_namespace
from common.models import db

PAGE_SIZE = 25
MAX_TRANSACTION = 500000
MAX_TRANSACTION_WITH_CONDITION = 10000
MAX_INTERNAL_TRANSACTION = 10000
MAX_TOKEN_TRANSFER = 10000

app_config = get_config()


@user_operation_namespace.route("/v1/explorer/ops")
class ExplorerUserOperations(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self):
        page_index = int(flask.request.args.get("page", 1))
        page_size = int(flask.request.args.get("size", 25))

        size = (page_index - 1) * page_size
        start_item = size + 1
        if start_item > MAX_TRANSACTION:
            return {"error": f"The requested data range exceeds the maximum({MAX_TRANSACTION}) allowed."}, 400

        sender = flask.request.args.get("sender")

        condition = True
        if sender:
            if not re.match(r"^0x[a-fA-F0-9]{40}$", sender):
                raise APIError("Invalid wallet address", code=400)
            condition = UserOperationResult.sender == sender

        user_operation_results = (
            db.session.query(UserOperationResult)
            .filter(condition)
            .order_by(
                UserOperationResult.block_number.desc(),
            )
            .limit(page_size)
            .offset(size)
            .all()
        )

        if sender:
            total_count = db.session.query(UserOperationResult).filter(condition).count()
        else:
            total_count = get_total_row_count("user_operations_results")

        if not user_operation_results:
            raise APIError("There are not any user operations", code=400)

        user_operation_result_list = []
        for user_operation_result in user_operation_results:
            user_operation_result_dict = {}
            user_operation_result_dict["user_op_hash"] = user_operation_result.user_op_hash
            user_operation_result_dict["block_timestamp"] = user_operation_result.block_timestamp
            user_operation_result_dict["status"] = user_operation_result.status
            user_operation_result_dict["sender"] = user_operation_result.sender
            user_operation_result_dict["transactions_hash"] = user_operation_result.transactions_hash
            user_operation_result_dict["block_number"] = user_operation_result.block_number
            wei_amount = user_operation_result.actual_gas_cost
            formatted_eth = format(wei_amount / 10**18, ".10f")
            user_operation_result_dict["fee"] = formatted_eth

            user_operation_result_list.append(
                {k: format_value_for_json(v) for k, v in user_operation_result_dict.items()}
            )

        return {
            "data": user_operation_result_list,
            "total": total_count,
            "max_display": min(
                MAX_TRANSACTION,
                total_count,
            ),
            "page": page_index,
            "size": page_size,
        }, 200


@user_operation_namespace.route("/v1/explorer/op/<hash>")
class ExplorerUserOperationDetails(Resource):
    @cache.cached(timeout=60, query_string=True)
    def get(self, hash):
        # parameter validated
        if not re.match(r"^0x[a-fA-F0-9]{64}$", hash):
            raise APIError("Invalid user operation hash", code=400)

        bytes_hash = hex_str_to_bytes(hash)

        user_operation_result = db.session.query(UserOperationResult).get(bytes_hash)
        if not user_operation_result:
            raise APIError("Cannot find user operation with hash", code=400)

        user_operation_result_dict = {}
        user_operation_result_dict["user_op_hash"] = user_operation_result.user_op_hash
        user_operation_result_dict["sender"] = user_operation_result.sender
        user_operation_result_dict["status"] = user_operation_result.status
        user_operation_result_dict["block_timestamp"] = user_operation_result.block_timestamp
        user_operation_result_dict["fee"] = format(user_operation_result.actual_gas_cost / 10**18, ".10f")

        user_operation_result_dict["gas_limit"] = (
            user_operation_result.call_gas_limit
            + user_operation_result.verification_gas_limit
            + user_operation_result.pre_verification_gas
        )
        user_operation_result_dict["gas_used"] = user_operation_result.actual_gas_used
        user_operation_result_dict["transactions_hash"] = user_operation_result.transactions_hash
        user_operation_result_dict["block_number"] = user_operation_result.block_number
        user_operation_result_dict["user_op_hash"] = user_operation_result.user_op_hash
        user_operation_result_dict["entry_point"] = (
            "0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789"  # todo: maybe there will be some new contract address?
        )
        user_operation_result_dict["call_gas_limit"] = user_operation_result.call_gas_limit
        user_operation_result_dict["verification_gas_limit"] = user_operation_result.verification_gas_limit
        user_operation_result_dict["pre_verification_gas"] = user_operation_result.pre_verification_gas
        user_operation_result_dict["max_fee_per_gas"] = user_operation_result.max_fee_per_gas
        user_operation_result_dict["max_priority_fee_per_gas"] = user_operation_result.max_priority_fee_per_gas
        user_operation_result_dict["bundler"] = user_operation_result.bundler
        user_operation_result_dict["paymaster"] = user_operation_result.paymaster
        user_operation_result_dict["sponsor_type"] = (
            1 if user_operation_result.paymaster != "0x0000000000000000000000000000000000000000" else 0
        )  # todo: add more types

        user_operation_result_dict["signature"] = user_operation_result.signature
        user_operation_result_dict["nonce"] = str(user_operation_result.nonce)
        user_operation_result_dict["call_data"] = user_operation_result.call_data

        result_json = {k: format_value_for_json(v) for k, v in user_operation_result_dict.items()}
        return result_json, 200


@user_operation_namespace.route("/v1/explorer/op/<hash>/token-transfers")
class ExplorerUserOperationTokenTransfers(Resource):
    @cache.cached(timeout=60, query_string=True)
    def get(self, hash):
        if not re.match(r"^0x[a-fA-F0-9]{64}$", hash):
            raise APIError("Invalid user operation hash", code=400)

        bytes_hash = hex_str_to_bytes(hash)

        user_operation_result = (
            db.session.query(UserOperationResult)
            .filter_by(user_op_hash=bytes_hash)
            .with_entities(
                UserOperationResult.transactions_hash,
                UserOperationResult.start_log_index,
                UserOperationResult.end_log_index,
            )
            .first()
        )

        erc20_token_transfers = (
            db.session.query(ERC20TokenTransfers)
            .filter(ERC20TokenTransfers.transaction_hash == user_operation_result.transactions_hash)
            .filter(
                (ERC20TokenTransfers.log_index > user_operation_result.start_log_index)
                & (ERC20TokenTransfers.log_index < user_operation_result.end_log_index)
            )
            .join(
                Tokens,  # not sure Erc20Tokens
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
            .filter(ERC721TokenTransfers.transaction_hash == user_operation_result.transactions_hash)
            .filter(
                (ERC721TokenTransfers.log_index > user_operation_result.start_log_index)
                & (ERC721TokenTransfers.log_index < user_operation_result.end_log_index)
            )
            .join(
                Tokens,  # Erc721Tokens
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
            .filter(ERC1155TokenTransfers.transaction_hash == user_operation_result.transactions_hash)
            .filter(
                (ERC1155TokenTransfers.log_index > user_operation_result.start_log_index)
                & (ERC1155TokenTransfers.log_index < user_operation_result.end_log_index)
            )
            .join(
                Tokens,  # Erc1155Tokens
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


@user_operation_namespace.route("/v1/explorer/op/<hash>/logs")
class ExplorerUserOperationLogs(Resource):
    @cache.cached(timeout=60, query_string=True)
    def get(self, hash):
        if not re.match(r"^0x[a-fA-F0-9]{64}$", hash):
            raise APIError("Invalid user operation hash", code=400)

        bytes_hash = hex_str_to_bytes(hash)

        user_operation_result = (
            db.session.query(UserOperationResult)
            .filter_by(user_op_hash=bytes_hash)
            .with_entities(
                UserOperationResult.transactions_hash,
                UserOperationResult.start_log_index,
                UserOperationResult.end_log_index,
            )
            .first()
        )

        logs = (
            db.session.query(Logs)
            .filter(Logs.transaction_hash == user_operation_result.transactions_hash)
            .filter(
                (Logs.log_index > user_operation_result.start_log_index)
                & (Logs.log_index < user_operation_result.end_log_index)
            )
            .join(Transactions, Logs.transaction_hash == Transactions.hash)
            .add_columns(Transactions.input)
            .all()
        )
        log_list = parse_log_with_transaction_input_list(logs)

        return {"total": len(log_list), "data": log_list}, 200


@user_operation_namespace.route("/v1/explorer/op/<hash>/raw")
class ExplorerUserOperationRaw(Resource):
    @cache.cached(timeout=60, query_string=True)
    def get(self, hash):
        if not re.match(r"^0x[a-fA-F0-9]{64}$", hash):
            raise APIError("Invalid user operation hash", code=400)
        bytes_hash = hex_str_to_bytes(hash)

        user_operation_result = db.session.query(UserOperationResult).get(bytes_hash)
        if not user_operation_result:
            raise APIError("Cannot find user operation with hash", code=400)

        user_operation_result_dict = {}
        user_operation_result_dict["sender"] = user_operation_result.sender
        user_operation_result_dict["nonce"] = str(user_operation_result.nonce)
        user_operation_result_dict["init_code"] = user_operation_result.init_code
        user_operation_result_dict["call_data"] = user_operation_result.call_data
        user_operation_result_dict["call_gas_limit"] = user_operation_result.call_gas_limit
        user_operation_result_dict["verification_gas_limit"] = user_operation_result.verification_gas_limit
        user_operation_result_dict["pre_verification_gas"] = user_operation_result.pre_verification_gas
        user_operation_result_dict["max_fee_per_gas"] = user_operation_result.max_fee_per_gas
        user_operation_result_dict["max_priority_fee_per_gas"] = user_operation_result.max_priority_fee_per_gas
        user_operation_result_dict["paymaster_and_data"] = user_operation_result.paymaster_and_data
        user_operation_result_dict["signature"] = user_operation_result.signature
        result_json = {k: format_value_for_json(v) for k, v in user_operation_result_dict.items()}
        return result_json, 200


@user_operation_namespace.route("/v1/explorer/transaction/<txn_hash>/ops")
class ExplorerTransactionOperation(Resource):
    @cache.cached(timeout=360, query_string=True)
    def get(self, txn_hash):
        if not re.match(r"^0x[a-fA-F0-9]{64}$", txn_hash):
            raise APIError("Invalid user operation hash", code=400)

        bytes_hash = hex_str_to_bytes(txn_hash)

        user_operation_result = db.session.query(UserOperationResult).filter_by(transactions_hash=bytes_hash)
        if not user_operation_result:
            raise APIError("Cannot find user operation with hash", code=400)

        user_operation_result_list = []
        for user_operation_result in user_operation_result:
            user_operation_result_dict = {}
            user_operation_result_dict["user_op_hash"] = user_operation_result.user_op_hash
            user_operation_result_dict["block_timestamp"] = user_operation_result.block_timestamp
            user_operation_result_dict["status"] = user_operation_result.status
            user_operation_result_dict["sender"] = user_operation_result.sender
            user_operation_result_dict["transactions_hash"] = user_operation_result.transactions_hash
            user_operation_result_dict["block_number"] = user_operation_result.block_number
            wei_amount = user_operation_result.actual_gas_cost
            formatted_eth = format(wei_amount / 10**18, ".10f")
            user_operation_result_dict["fee"] = formatted_eth
            user_operation_result_dict["nonce"] = str(user_operation_result.nonce)
            user_operation_result_dict["init_code"] = user_operation_result.init_code
            user_operation_result_dict["call_data"] = user_operation_result.call_data
            user_operation_result_dict["call_gas_limit"] = user_operation_result.call_gas_limit
            user_operation_result_dict["verification_gas_limit"] = user_operation_result.verification_gas_limit
            user_operation_result_dict["pre_verification_gas"] = user_operation_result.pre_verification_gas
            user_operation_result_dict["max_fee_per_gas"] = user_operation_result.max_fee_per_gas
            user_operation_result_dict["max_priority_fee_per_gas"] = user_operation_result.max_priority_fee_per_gas
            user_operation_result_dict["paymaster_and_data"] = user_operation_result.paymaster_and_data
            user_operation_result_dict["signature"] = user_operation_result.signature

            user_operation_result_list.append(
                {k: format_value_for_json(v) for k, v in user_operation_result_dict.items()}
            )
        return user_operation_result_list, 200
