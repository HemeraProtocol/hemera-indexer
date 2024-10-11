import binascii
import re
from datetime import timedelta
from operator import or_

from flask import request
from flask_restx import Resource
from sqlalchemy import and_, func

from api.app import explorer
from api.app.cache import cache
from api.app.l2_explorer import l2_explorer_namespace
from api.app.utils.utils import is_l1_block_finalized
from common.models import db as postgres_db
from common.models.blocks import Blocks  # DailyBridgeTransactionsAggregates,
from common.models.bridge import (
    ArbitrumStateBatches,
    ArbitrumTransactionBatches,
    BridgeTokens,
    L1ToL2BridgeTransactions,
    L2ToL1BridgeTransactions,
    LineaBatches,
    MantleDAStores,
    MantleDAStoreTransactionMapping,
    OpBedrockStateBatches,
    OpDATransactions,
    StateBatches,
    ZkEvmBatches,
)
from common.models.scheduled_metadata import ScheduledWalletCountMetadata
from common.models.tokens import Tokens
from common.models.transactions import Transactions
from common.utils.bridge_utils import BridgeTransactionParser
from common.utils.config import get_config
from common.utils.exception_control import APIError
from common.utils.format_utils import as_dict, format_to_dict, format_value_for_json
from common.utils.web3_utils import is_eth_address

app_config = get_config()

PAGE_SIZE = 25
MAX_TRANSACTION = 500000
MAX_TRANSACTION_WITH_CONDITION = 10000
MAX_INTERNAL_TRANSACTION = 10000
MAX_TOKEN_TRANSFER = 10000

bridge_transaction_parser = BridgeTransactionParser.init_from_config(get_config())


def get_filter_condition_and_total_block_count(state_batch, batch):
    if state_batch:
        if app_config.l2_config.rollup_type == "op":
            state_batch = (
                postgres_db.session.query(OpBedrockStateBatches)
                .filter(OpBedrockStateBatches.batch_index == state_batch)
                .first()
            )
            if state_batch:
                filter_condition = and_(
                    Blocks.number >= state_batch.start_block_number,
                    Blocks.number <= state_batch.end_block_number,
                )
                total_blocks = state_batch.block_count
            else:
                raise APIError("Batch not exist", code=400)
        elif app_config.l2_config.rollup_type == "arbitrum":
            state_batch = (
                postgres_db.session.query(ArbitrumStateBatches)
                .filter(ArbitrumStateBatches.node_num == state_batch)
                .first()
            )
            if state_batch:
                filter_condition = and_(
                    Blocks.number >= state_batch.start_block_number,
                    Blocks.number <= state_batch.end_block_number,
                )
                total_blocks = state_batch.block_count
            else:
                raise APIError("Batch not exist", code=400)
        else:
            state_batch = (
                postgres_db.session.query(StateBatches)
                .with_entities(
                    StateBatches.previous_total_elements,
                    StateBatches.batch_size,
                )
                .filter(StateBatches.batch_index == state_batch)
                .first()
            )

            if state_batch:
                filter_condition = and_(
                    Blocks.number > state_batch.previous_total_elements,
                    Blocks.number <= (state_batch.previous_total_elements + state_batch.batch_size),
                )
                total_blocks = state_batch.batch_size
            else:
                raise APIError("Batch not exist", code=400)
    elif batch:
        if app_config.chain == "zkevm":
            batch = (
                postgres_db.session.query(ZkEvmBatches)
                .with_entities(ZkEvmBatches.batch_index)
                .filter(ZkEvmBatches.batch_index == batch)
                .first()
            )
            if batch:
                pass
            else:
                raise APIError("Batch not exist", code=400)
        elif app_config.chain == "linea":
            batch = (
                postgres_db.session.query(LineaBatches)
                .with_entities(
                    LineaBatches.number,
                    LineaBatches.blocks,
                    LineaBatches.block_count,
                )
                .filter(LineaBatches.number == batch)
                .first()
            )
            if batch:
                filter_condition = Blocks.number.in_(batch.blocks)
                total_blocks = batch.block_count
            else:
                raise APIError("Batch not exist", code=400)
    return (filter_condition, total_blocks)


def set_l2_extra_info_by_transaction_hash(transaction_json):

    if app_config.chain == "zkevm":
        batch = (
            postgres_db.session.query(ZkEvmBatches)
            .with_entities(
                ZkEvmBatches.number,
                ZkEvmBatches.sequence_batch_tx_hash,
                ZkEvmBatches.verify_batch_tx_hash,
            )
            .filter(
                ZkEvmBatches.start_block_number <= transaction_json["block_number"],
                ZkEvmBatches.end_block_number >= transaction_json["block_number"],
            )
            .first()
        )
        if batch:
            transaction_json["batch_number"] = batch.number
            transaction_json["send_sequences_tx_hash"] = batch.sequence_batch_tx_hash
            transaction_json["verify_batch_tx_hash"] = batch.verify_batch_tx_hash
    elif app_config.chain == "linea":
        pass
    elif app_config.l2_config.rollup_type == "op":
        state_batch = (
            OpBedrockStateBatches.query.with_entities(
                OpBedrockStateBatches.batch_index,
                OpBedrockStateBatches.l1_transaction_hash,
            )
            .filter(
                OpBedrockStateBatches.start_block_number <= transaction_json["block_number"],
                OpBedrockStateBatches.end_block_number >= transaction_json["block_number"],
            )
            .first()
        )
        if state_batch:
            transaction_json["state_batch_index"] = state_batch.batch_index
            transaction_json["state_batch_transaction_hash"] = state_batch.l1_transaction_hash
    elif app_config.chain == "mantle":
        state_batch = (
            StateBatches.query.with_entities(
                StateBatches.batch_index,
                StateBatches.l1_transaction_hash,
            )
            .filter(
                StateBatches.previous_total_elements < transaction_json["block_number"],
            )
            .order_by(StateBatches.batch_index.desc())
            .first()
        )
        if state_batch:
            transaction_json["state_batch_index"] = state_batch.batch_index
            transaction_json["state_batch_transaction_hash"] = state_batch.l1_transaction_hash

        da_batch_record = MantleDAStoreTransactionMapping.query.filter(
            MantleDAStoreTransactionMapping.transaction_hash == transaction_json["hash"]
        ).first()
        if da_batch_record:
            da_batch = (
                MantleDAStores.query.with_entities(MantleDAStores.batch_index, MantleDAStores.msg_hash)
                .filter(MantleDAStores.id == da_batch_record.data_store_id)
                .first()
            )
            if da_batch:
                transaction_json["da_batch_index"] = da_batch.batch_index
                transaction_json["da_batch_msg_hash"] = da_batch.msg_hash


def generate_transaction_filter_by_batch(batch, state_batch, da_batch):
    filter_condition, total_records = True, 0
    if batch:
        if app_config.chain == "zkevm":
            batch = (
                postgres_db.session.query(ZkEvmBatches)
                .with_entities(
                    ZkEvmBatches.batch_index,
                    ZkEvmBatches.block_count,
                    ZkEvmBatches.transaction_count,
                    ZkEvmBatches.start_block_number,
                    ZkEvmBatches.end_block_number,
                    ZkEvmBatches.transactions,
                )
                .filter(ZkEvmBatches.batch_index == batch)
                .first()
            )
            if batch:
                filter_condition = and_(
                    Transactions.block_number >= batch.start_block_number,
                    Transactions.block_number <= batch.end_block_number,
                )
                total_records = batch.transaction_count
            else:
                raise APIError("Batch not exist", code=400)
        elif app_config.chain == "linea":
            batch = (
                postgres_db.session.query(LineaBatches)
                .with_entities(
                    LineaBatches.number,
                    LineaBatches.block_count,
                    LineaBatches.tx_count,
                    LineaBatches.last_finalized_block_number,
                )
                .filter(LineaBatches.number == batch)
                .first()
            )
            if batch:
                filter_condition = and_(
                    Transactions.block_number > batch.last_finalized_block_number - batch.block_count,
                    Transactions.block_number <= batch.last_finalized_block_number,
                )
                total_records = batch.tx_count
            else:
                raise APIError("Batch not exist", code=400)
    elif state_batch:
        if app_config.l2_config.rollup_type == "op":
            state_batch = (
                postgres_db.session.query(OpBedrockStateBatches)
                .filter(OpBedrockStateBatches.batch_index == state_batch)
                .first()
            )
            if state_batch:
                filter_condition = and_(
                    Transactions.block_number >= state_batch.start_block_number,
                    Transactions.block_number <= state_batch.end_block_number,
                )
                total_records = state_batch.transaction_count
            else:
                raise APIError("Batch not exist", code=400)
        elif app_config.l2_config.rollup_type == "arbitrum":
            state_batch = (
                postgres_db.session.query(ArbitrumStateBatches)
                .filter(ArbitrumStateBatches.node_num == state_batch)
                .first()
            )
            if state_batch:
                filter_condition = and_(
                    Transactions.block_number >= state_batch.start_block_number,
                    Transactions.block_number <= state_batch.end_block_number,
                )
                total_records = state_batch.transaction_count
            else:
                raise APIError("Batch not exist", code=400)
        else:
            state_batch = (
                postgres_db.session.query(StateBatches)
                .with_entities(
                    StateBatches.previous_total_elements,
                    StateBatches.batch_size,
                )
                .filter(StateBatches.batch_index == state_batch)
                .first()
            )
            if state_batch:
                filter_condition = and_(
                    Transactions.block_number > state_batch.previous_total_elements,
                    Transactions.block_number <= (state_batch.previous_total_elements + state_batch.batch_size),
                )
                total_records = state_batch.batch_size
            else:
                raise APIError("Batch not exist", code=400)
    elif da_batch:
        if app_config.l2_config.rollup_type == "arbitrum":
            da_batch = ArbitrumTransactionBatches.query.filter(
                ArbitrumTransactionBatches.l1_transaction_hash == da_batch
            ).first()
            if not da_batch:
                raise APIError("Batch not exist", code=400)
            filter_condition = and_(
                Transactions.block_number >= da_batch.start_block_number,
                Transactions.block_number <= da_batch.end_block_number,
            )
            total_records = da_batch.transaction_count
        else:
            da_batch = MantleDAStores.query.filter(MantleDAStores.batch_index == da_batch).first()
            if not da_batch:
                raise APIError("Batch not exist", code=400)
            transactions = (
                MantleDAStoreTransactionMapping.query.with_entities(MantleDAStoreTransactionMapping.transaction_hash)
                .filter(MantleDAStoreTransactionMapping.data_store_id == da_batch.id)
                .all()
            )
            filter_condition = Transactions.hash.in_(list(map(lambda x: x.transaction_hash, transactions)))
            total_records = da_batch.tx_count

    return filter_condition, total_records


def get_latest_batch_index():
    if app_config.chain == "zkevm":
        lastest_batch = (
            postgres_db.session.query(ZkEvmBatches)
            .with_entities(ZkEvmBatches.batch_index)
            .order_by(ZkEvmBatches.batch_index.desc())
            .first()
        )
        if lastest_batch:
            lastest_batch_number = lastest_batch.batch_index
        else:
            lastest_batch_number = 0

    elif app_config.l2_config.rollup_type == "op":
        lastest_batch = (
            postgres_db.session.query(OpBedrockStateBatches)
            .with_entities(OpBedrockStateBatches.batch_index)
            .order_by(OpBedrockStateBatches.batch_index.desc())
            .first()
        )
        if lastest_batch:
            lastest_batch_number = lastest_batch.batch_index
        else:
            lastest_batch_number = 0
    elif app_config.chain == "linea":
        lastest_batch = (
            postgres_db.session.query(LineaBatches)
            .with_entities(LineaBatches.number)
            .order_by(LineaBatches.number.desc())
            .first()
        )
        if lastest_batch:
            lastest_batch_number = lastest_batch.number
        else:
            lastest_batch_number = 0

        return lastest_batch_number


def get_deposit_count_by_address(address):
    address_bin = binascii.unhexlify(address[2:])
    last_timestamp = postgres_db.session.query(func.max(ScheduledWalletCountMetadata.last_data_timestamp)).scalar()
    recently_txn_count = (
        postgres_db.session.query(L1ToL2BridgeTransactions.l1_transaction_hash)
        .filter(
            and_(
                (
                    L1ToL2BridgeTransactions.l1_block_timestamp >= last_timestamp.date()
                    if last_timestamp is not None
                    else True
                ),
                L1ToL2BridgeTransactions.to_address == address_bin,
            )
        )
        .count()
    )
    result = (
        postgres_db.session.query(explorer.models.WalletAddresses)
        .with_entities(explorer.models.WalletAddresses.deposit_cnt)
        .filter(explorer.models.WalletAddresses.address == address)
        .first()
    )
    past_txn_count = 0 if not result else result[0]
    total_count = past_txn_count + recently_txn_count
    return total_count


def get_withdraw_count_by_address(address):
    address_bin = binascii.unhexlify(address[2:])
    last_timestamp = postgres_db.session.query(func.max(ScheduledWalletCountMetadata.last_data_timestamp)).scalar()
    recently_txn_count = (
        postgres_db.session.query(L2ToL1BridgeTransactions.l2_transaction_hash)
        .filter(
            and_(
                (
                    L2ToL1BridgeTransactions.l2_block_timestamp >= last_timestamp.date()
                    if last_timestamp is not None
                    else True
                ),
                L2ToL1BridgeTransactions.from_address == address_bin,
            )
        )
        .count()
    )
    result = (
        postgres_db.session.query(explorer.models.WalletAddresses)
        .with_entities(explorer.models.WalletAddresses.withdraw_cnt)
        .filter(explorer.models.WalletAddresses.address == address)
        .first()
    )
    past_txn_count = 0 if not result else result[0]
    total_count = past_txn_count + recently_txn_count
    return total_count


def get_total_deposit_txn_count():
    latest_record = (
        DailyBridgeTransactionsAggregates.query.with_entities(
            func.max(DailyBridgeTransactionsAggregates.block_date),
            func.sum(DailyBridgeTransactionsAggregates.deposit_cnt),
        )
        .group_by(DailyBridgeTransactionsAggregates.block_date)
        .first()
    )
    # Check if the query returned a result
    if latest_record is None:
        return L1ToL2BridgeTransactions.query.count()

    block_date, cumulate_count = latest_record

    # Count transactions since the latest block date
    cnt = L1ToL2BridgeTransactions.query.filter(
        and_(
            L1ToL2BridgeTransactions.l1_block_timestamp >= (block_date + timedelta(days=1)),
            L1ToL2BridgeTransactions.l1_transaction_hash is not None,
        )
    ).count()

    return int(cnt + cumulate_count)


def get_total_withdraw_txn_count():
    latest_record = (
        DailyBridgeTransactionsAggregates.query.with_entities(
            func.max(DailyBridgeTransactionsAggregates.block_date),
            func.sum(DailyBridgeTransactionsAggregates.withdraw_cnt),
        )
        .group_by(DailyBridgeTransactionsAggregates.block_date)
        .first()
    )
    # Check if the query returned a result
    if latest_record is None:
        return L2ToL1BridgeTransactions.query.count()

    block_date, cumulate_count = latest_record

    # Count transactions since the latest block date
    cnt = L2ToL1BridgeTransactions.query.filter(
        and_(
            L2ToL1BridgeTransactions.l2_block_timestamp >= (block_date + timedelta(days=1)),
            L2ToL1BridgeTransactions.l2_transaction_hash is not None,
        )
    ).count()

    return int(cnt + cumulate_count)


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
            total_records = get_total_deposit_txn_count()
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
            total_records = get_total_withdraw_txn_count()
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


@l2_explorer_namespace.route("/v1/explorer/state_batches")
class ExplorerStateBatches(Resource):
    @cache.cached(timeout=60, query_string=True)
    def get(self):
        page_index = int(request.args.get("page", 1))
        page_size = int(request.args.get("size", PAGE_SIZE))
        if page_index <= 0 or page_size <= 0:
            raise APIError("Invalid page or size", code=400)

        rollup_type = app_config.l2_config.rollup_type
        batch_list = []
        total_batches = 0

        if rollup_type == "op":
            table = OpBedrockStateBatches
            order_by_field = table.batch_index
        elif rollup_type == "arbitrum":
            table = ArbitrumStateBatches
            order_by_field = table.node_num
        else:
            table = StateBatches
            order_by_field = table.batch_index

        batches = (
            postgres_db.session.query(table)
            .order_by(order_by_field.desc())
            .limit(page_size)
            .offset((page_index - 1) * page_size)
            .all()
        )

        lastest_batch = table.query.with_entities(order_by_field).order_by(order_by_field.desc()).first()
        if lastest_batch:
            total_batches = lastest_batch[0] if rollup_type == "arbitrum" else lastest_batch.batch_index

        for batch in batches:
            batch_json = as_dict(batch)
            batch_json["status"] = 2
            # Temporary format the data
            if rollup_type == "arbitrum":
                # Temporary format the data
                batch_json["status"] = 2 if batch.l1_transaction_hash else 3
                batch_json["batch_index"] = batch.node_num
                batch_json["batch_root"] = batch.node_hash
                if not batch.l1_transaction_hash:
                    batch_json["l1_transaction_hash"] = batch.create_l1_transaction_hash
                    batch_json["l1_block_timestamp"] = format_value_for_json(batch.create_l1_block_timestamp)
                    batch_json["l1_block_hash"] = batch.create_l1_block_hash
                    batch_json["l1_transaction_hash"] = batch.create_l1_transaction_hash

            batch_list.append(batch_json)

        return {
            "data": batch_list,
            "total": total_batches,
            "page": page_index,
            "size": page_size,
        }, 200


@l2_explorer_namespace.route("/v1/explorer/state_batch/<batch_index>")
class ExplorerStateBatchDetail(Resource):
    @cache.cached(timeout=60, query_string=True)
    def get(self, batch_index):
        if app_config.l2_config.rollup_type == "op":
            table = OpBedrockStateBatches
        elif app_config.l2_config.rollup_type == "arbitrum":
            table = ArbitrumStateBatches
        else:
            table = StateBatches

        batch = postgres_db.session.query(table).get(batch_index)
        if not batch:
            raise APIError("Cannot find batch with batch number", code=400)

        batch_json = as_dict(batch)
        batch_json["status"] = 2
        if table == StateBatches:
            batch_json["transaction_count"] = batch_json["batch_size"]
            batch_json["block_count"] = batch_json["batch_size"]

        if app_config.l2_config.rollup_type == "arbitrum":
            lastest_batch = postgres_db.session.query(table).order_by(table.node_num.desc()).first()
            batch_json["is_last_batch"] = lastest_batch.node_num == batch.node_num

            # Temporary format the data
            batch_json["status"] = 2 if batch.l1_transaction_hash else 3
            batch_json["batch_index"] = batch.node_num
            batch_json["batch_root"] = batch.node_hash
            if not batch.l1_transaction_hash:
                batch_json["l1_transaction_hash"] = batch.create_l1_transaction_hash
                batch_json["l1_block_timestamp"] = batch.create_l1_block_timestamp
                batch_json["l1_block_hash"] = batch.create_l1_block_hash
                batch_json["l1_transaction_hash"] = batch.create_l1_transaction_hash
        else:
            lastest_batch = postgres_db.session.query(table).order_by(table.batch_index.desc()).first()
            batch_json["is_last_batch"] = lastest_batch.batch_index == batch.batch_index
        return batch_json, 200


@l2_explorer_namespace.route("/v1/explorer/linea_batches")
class ExplorerBatchess(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self):
        page_index = int(request.args.get("page", 1))
        page_size = int(request.args.get("size", PAGE_SIZE))
        if page_index <= 0 or page_size <= 0:
            raise APIError("Invalid page or size", code=400)

        batches = (
            postgres_db.session.query(LineaBatches)
            .order_by(LineaBatches.number.desc())
            .limit(page_size)
            .offset((page_index - 1) * page_size)
            .all()
        )
        batch_list = []
        for batch in batches:
            batch_json = as_dict(batch)
            batch_json["status"] = 2 if is_l1_block_finalized(batch.verify_block_number, batch.timestamp) else 0
            batch_json["transaction_count"] = batch.tx_count
            batch_json["block_count"] = batch.block_count
            batch_list.append(batch_json)

        lastest_batch = (
            postgres_db.session.query(LineaBatches)
            .with_entities(LineaBatches.number)
            .order_by(LineaBatches.number.desc())
            .first()
        )
        if lastest_batch:
            total_batches = lastest_batch.number
        else:
            total_batches = 0

        return {
            "data": batch_list,
            "total": total_batches,
            "page": page_index,
            "size": page_size,
        }, 200


@l2_explorer_namespace.route("/v1/explorer/linea_batch/<number>")
class ExplorerBatchDetail(Resource):
    @cache.cached(timeout=60, query_string=True)
    def get(self, number):
        batch = postgres_db.session.query(LineaBatches).get(number)

        if batch:
            batch_json = as_dict(batch)
            batch_json["status"] = 2 if is_l1_block_finalized(batch.verify_block_number, batch.timestamp) else 0
            batch_json["transaction_count"] = batch.tx_count
            batch_json["block_count"] = batch.block_count

            lastest_batch = postgres_db.session.query(LineaBatches).order_by(LineaBatches.number.desc()).first()
            batch_json["is_last_batch"] = lastest_batch.number == batch.number
            return batch_json, 200
        else:
            raise APIError("Cannot find batch with batch number", code=400)


@l2_explorer_namespace.route("/v1/explorer/batches")
class ExplorerBatchess(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self):
        page_index = int(request.args.get("page", 1))
        page_size = int(request.args.get("size", PAGE_SIZE))
        if page_index <= 0 or page_size <= 0:
            raise APIError("Invalid page or size", code=400)
        status = request.args.get("status", None)  # 0->Pending 1->L1 Sequence Confirmed 2->Finalized

        filter_condition = True
        if status:
            if int(status) == 0:
                filter_condition = ZkEvmBatches.sequence_batch_tx_hash == None
            elif int(status) == 1:
                filter_condition = ZkEvmBatches.sequence_batch_tx_hash != None
            elif int(status) == 2:
                filter_condition = ZkEvmBatches.verify_batch_tx_hash != None
        batches = (
            postgres_db.session.query(ZkEvmBatches)
            .order_by(ZkEvmBatches.batch_index.desc())
            .filter(filter_condition)
            .limit(page_size)
            .offset((page_index - 1) * page_size)
            .all()
        )
        batch_list = []
        for batch in batches:
            batch_json = as_dict(batch)
            batch_json["status"] = (
                0 if batch.sequence_batch_tx_hash == None else 2 if batch.verify_batch_tx_hash != None else 1
            )
            batch_json["transaction_count"] = batch.transaction_count
            batch_list.append(batch_json)

        latest_batch = (
            postgres_db.session.query(ZkEvmBatches)
            .with_entities(ZkEvmBatches.batch_index)
            .order_by(ZkEvmBatches.batch_index.desc())
            .first()
        )
        if latest_batch:
            total_batches = latest_batch.batch_index
        else:
            total_batches = 0

        return {
            "data": batch_list,
            "total": total_batches,
            "page": page_index,
            "size": page_size,
        }, 200


@l2_explorer_namespace.route("/v1/explorer/batch/<batch_index>")
class ExplorerBatchDetail(Resource):
    @cache.cached(timeout=60, query_string=True)
    def get(self, batch_index):
        batch = postgres_db.session.query(ZkEvmBatches).get(batch_index)

        if batch:
            batch_json = as_dict(batch)
            batch_json["status"] = (
                0 if batch.sequence_batch_tx_hash == None else 2 if batch.verify_batch_tx_hash != None else 1
            )
            batch_json["transaction_count"] = batch.transaction_count

            latest_batch = postgres_db.session.query(ZkEvmBatches).order_by(ZkEvmBatches.batch_index.desc()).first()
            batch_json["is_last_batch"] = latest_batch.batch_index == batch.batch_index
            return batch_json, 200
        else:
            raise APIError("Cannot find batch with batch number", code=400)


@l2_explorer_namespace.route("/v1/explorer/da_batches")
class ExplorerDABatches(Resource):
    def get(self):
        page_index = int(request.args.get("page", 1))
        page_size = int(request.args.get("size", PAGE_SIZE))
        if page_index <= 0 or page_size <= 0:
            raise APIError("Invalid page or size", code=400)
        if app_config.l2_config.rollup_type == "arbitrum":
            batches = (
                postgres_db.session.query(ArbitrumTransactionBatches)
                .order_by(
                    ArbitrumTransactionBatches.l1_block_number.desc(),
                    ArbitrumTransactionBatches.batch_index.desc(),
                )
                .limit(page_size)
                .offset((page_index - 1) * page_size)
                .all()
            )
            total_cnt = postgres_db.session.query(ArbitrumTransactionBatches).count()
        else:
            batches = (
                postgres_db.session.query(OpDATransactions)
                .order_by(
                    OpDATransactions.block_number.desc(),
                    OpDATransactions.transaction_index.desc(),
                )
                .limit(page_size)
                .offset((page_index - 1) * page_size)
                .all()
            )
            total_cnt = postgres_db.session.query(OpDATransactions).count()
        batch_list = []
        for batch in batches:
            batch_json = as_dict(batch)
            if app_config.l2_config.rollup_type == "op":
                if app_config.l2_config.da_config.da_type == "plasma":
                    batch_json["da_commitment"] = batch.input[0:2] + batch.input[4:]
                    batch_json["da_url"] = (
                        app_config.l2_config.da_config.plasma_api_endpoint + batch_json["da_commitment"]
                    )
                elif app_config.l2_config.da_config.da_type == "blob":
                    batch_json["da_commitment"] = batch.blob_versioned_hashes[0]
                    batch_json["da_url"] = (
                        app_config.l2_config.da_config.blob_scan_endpoint + batch.blob_versioned_hashes[0]
                    )
                else:
                    pass
            elif app_config.l2_config.rollup_type == "arbitrum":
                # Temporary format
                batch_json["block_number"] = batch_json["l1_block_number"]
                batch_json["hash"] = batch_json["l1_transaction_hash"]
                batch_json["block_timestamp"] = batch_json["l1_block_timestamp"]
                batch_json["da_commitment"] = batch_json["batch_root"]

            batch_list.append(batch_json)

        return {
            "data": batch_list,
            "total": total_cnt,
            "page": page_index,
            "size": page_size,
        }, 200


@l2_explorer_namespace.route("/v1/explorer/da_batch/<batch_index_or_hash>")
class ExplorerDABatchDetail(Resource):
    @cache.cached(timeout=60, query_string=True)
    def get(self, batch_index_or_hash):
        if app_config.l2_config.rollup_type == "arbitrum":
            pass
        else:
            if batch_index_or_hash.isnumeric():
                batch = MantleDAStores.query.filter(MantleDAStores.batch_index == batch_index_or_hash).first()
            else:
                batch = MantleDAStores.query.filter(MantleDAStores.msg_hash == batch_index_or_hash).first()
            if not batch:
                raise APIError("Cannot find batch with batch number", code=400)

        batch_json = as_dict(batch)
        return batch_json, 200
