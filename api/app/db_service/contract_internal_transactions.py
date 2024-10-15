from common.models import db
from common.models.contract_internal_transactions import ContractInternalTransactions
from common.utils.db_utils import build_entities
from common.utils.format_utils import hex_str_to_bytes


def get_internal_transactions_by_transaction_hash(transaction_hash, columns="*"):
    transaction_hash = hex_str_to_bytes(transaction_hash.lower())
    entities = build_entities(ContractInternalTransactions, columns)

    transactions = (
        db.session.query(ContractInternalTransactions)
        .with_entities(*entities)
        .order_by(
            ContractInternalTransactions.block_number.desc(),
            ContractInternalTransactions.transaction_index.desc(),
        )
        .filter(ContractInternalTransactions.transaction_hash == transaction_hash)
        .all()
    )
    return transactions


def get_internal_transactions_by_condition(columns="*", filter_condition=None, limit=1, offset=0):
    entities = build_entities(ContractInternalTransactions, columns)

    transactions = (
        db.session.query(ContractInternalTransactions)
        .with_entities(*entities)
        .order_by(
            ContractInternalTransactions.block_number.desc(),
            ContractInternalTransactions.transaction_index.desc(),
        )
        .filter(filter_condition)
        .limit(limit)
        .offset(offset)
        .all()
    )
    return transactions


def get_internal_transactions_cnt_by_condition(columns="*", filter_condition=None):
    entities = build_entities(ContractInternalTransactions, columns)
    count = db.session.query(ContractInternalTransactions).with_entities(*entities).filter(filter_condition).count()

    return count
