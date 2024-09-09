import flask
from flask_restx import Resource

from api.app.cache import cache
from api.app.db_service.af_token_deposit import (
    get_deposit_assets_list,
    get_deposit_chain_list,
    get_transactions_by_condition,
    get_transactions_cnt_by_condition,
    get_transactions_cnt_by_wallet,
)
from api.app.db_service.blocks import get_block_by_hash
from api.app.deposit_to_l2 import token_deposit_namespace
from api.app.utils.parse_utils import parse_deposit_assets, parse_deposit_transactions
from common.utils.config import get_config
from common.utils.exception_control import APIError
from common.utils.format_utils import row_to_dict
from common.utils.web3_utils import SUPPORT_CHAINS, chain_id_name_mapping
from indexer.modules.custom.deposit_to_l2.models.af_token_deposits__transactions import AFTokenDepositsTransactions

MAX_TRANSACTION = 500000
MAX_TRANSACTION_WITH_CONDITION = 10000

app_config = get_config()


@token_deposit_namespace.route("/v1/aci/deposit/transactions")
class ExplorerDepositTransactions(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self):
        page_index = int(flask.request.args.get("page", 1))
        page_size = int(flask.request.args.get("size", 25))
        if page_index <= 0 or page_size <= 0:
            raise APIError("Invalid page or size", code=400)

        if page_index * page_size > MAX_TRANSACTION:
            raise APIError(f"Showing the last {MAX_TRANSACTION} records only", code=400)

        wallet_address = flask.request.args.get("wallet_address", None)
        chain = flask.request.args.get("chain", None)
        contract = flask.request.args.get("contract", None)
        token = flask.request.args.get("token", None)
        block = flask.request.args.get("block", None)

        has_filter = False
        if wallet_address or chain or contract or token or block:
            has_filter = True
            if page_index * page_size > MAX_TRANSACTION_WITH_CONDITION:
                raise APIError(
                    f"Showing the last {MAX_TRANSACTION_WITH_CONDITION} records only",
                    code=400,
                )

        filter_condition = True

        if wallet_address:
            wallet_address = wallet_address.lower()
            bytes_wallet_address = bytes.fromhex(wallet_address[2:])
            filter_condition = AFTokenDepositsTransactions.wallet_address == bytes_wallet_address

        elif chain:
            if chain.isnumeric():
                filter_condition = AFTokenDepositsTransactions.chain_id == chain
            else:
                if chain not in SUPPORT_CHAINS:
                    raise APIError(
                        f"{chain} is not supported yet, it will coming soon.",
                        code=400,
                    )

                chain_id = SUPPORT_CHAINS[chain]["chain_id"]
                filter_condition = AFTokenDepositsTransactions.chain_id == chain_id

        elif contract:
            contract = contract.lower()
            bytes_contract = bytes.fromhex(contract[2:])
            filter_condition = AFTokenDepositsTransactions.contract == bytes_contract

        elif token:
            token = token.lower()
            bytes_token = bytes.fromhex(token[2:])
            filter_condition = AFTokenDepositsTransactions.token == bytes_token

        elif block:
            if block.isnumeric():
                filter_condition = AFTokenDepositsTransactions.block_number == int(block)
            else:
                block_number = get_block_by_hash(hash=block, columns=["number"])
                filter_condition = AFTokenDepositsTransactions.block_number == block_number

        total_records = get_transactions_cnt_by_condition(filter_condition=filter_condition)
        transactions = get_transactions_by_condition(
            filter_condition=filter_condition,
            columns=[
                "transaction_hash",
                "wallet_address",
                "chain_id",
                "contract_address",
                "token_address",
                "value",
                "block_number",
                "block_timestamp",
            ],
            limit=page_size,
            offset=(page_index - 1) * page_size,
        )

        transaction_list = parse_deposit_transactions(transactions)

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


@token_deposit_namespace.route("/v1/aci/<wallet_address>/deposit/current")
class ExplorerDepositCurrent(Resource):

    @cache.cached(timeout=10, query_string=True)
    def get(self, wallet_address):
        if wallet_address is None:
            raise APIError(
                f"parameter 'wallet_address' are required",
                code=400,
            )

        deposit_times = get_transactions_cnt_by_wallet(wallet_address)

        chains = get_deposit_chain_list(wallet_address)
        chain_list = [chain_id_name_mapping[row_to_dict(chain)["chain_id"]] for chain in chains]

        assets = get_deposit_assets_list(wallet_address)
        asset_list = parse_deposit_assets(assets)

        return {
            "wallet_address": wallet_address,
            "deposit_times": deposit_times,
            "chain_list": chain_list,
            "asset_list": asset_list,
        }, 200


@token_deposit_namespace.route("/v1/aci/<wallet_address>/deposit/bridge_times")
class ExplorerDepositBridgeTimes(Resource):

    @cache.cached(timeout=10, query_string=True)
    def get(self, wallet_address):
        if wallet_address is None:
            raise APIError(
                f"parameter 'wallet_address' are required",
                code=400,
            )

        times = get_transactions_cnt_by_wallet(wallet_address)

        return {
            "wallet_address": wallet_address,
            "bridge_times": times,
        }, 200


@token_deposit_namespace.route("/v1/aci/<wallet_address>/deposit/chain_list")
class ExplorerDepositChainList(Resource):

    @cache.cached(timeout=10, query_string=True)
    def get(self, wallet_address):
        if wallet_address is None:
            raise APIError(
                f"parameter 'wallet_address' are required",
                code=400,
            )

        chains = get_deposit_chain_list(wallet_address)

        chain_list = [chain_id_name_mapping[row_to_dict(chain)["chain_id"]] for chain in chains]
        return {
            "wallet_address": wallet_address,
            "chain_list": chain_list,
        }, 200


@token_deposit_namespace.route("/v1/aci/<wallet_address>/deposit/assets_list")
class ExplorerDepositAssetsList(Resource):

    @cache.cached(timeout=10, query_string=True)
    def get(self, wallet_address):
        if wallet_address is None:
            raise APIError(
                f"parameter 'wallet_address' are required",
                code=400,
            )

        assets = get_deposit_assets_list(wallet_address)
        asset_list = parse_deposit_assets(assets)
        return {
            "wallet_address": wallet_address,
            "asset_list": asset_list,
        }, 200