from api.app.db_service.tokens import get_token_by_address
from common.models import db
from common.utils.db_utils import build_entities
from common.utils.format_utils import row_to_dict
from common.utils.web3_utils import chain_id_name_mapping
from indexer.modules.custom.deposit_to_l2.models.af_token_deposits__transactions import AFTokenDepositsTransactions
from indexer.modules.custom.deposit_to_l2.models.af_token_deposits_current import AFTokenDepositsCurrent


def get_transactions_by_condition(filter_condition=None, columns="*", limit=None, offset=None):
    entities = build_entities(AFTokenDepositsTransactions, columns)

    statement = db.session.query(AFTokenDepositsTransactions).with_entities(*entities)

    if filter_condition is not None:
        statement = statement.filter(filter_condition)

    statement = statement.order_by(AFTokenDepositsTransactions.block_number.desc())

    if limit is not None:
        statement = statement.limit(limit)

    if offset is not None:
        statement = statement.offset(offset)

    return statement.all()


def get_transactions_cnt_by_condition(filter_condition=None, columns="*"):
    entities = build_entities(AFTokenDepositsTransactions, columns)

    count = db.session.query(AFTokenDepositsTransactions).with_entities(*entities).filter(filter_condition).count()

    return count


def get_transactions_cnt_by_wallet(wallet_address):
    wallet_address = wallet_address.lower()
    bytes_wallet_address = bytes.fromhex(wallet_address[2:])

    count = get_transactions_cnt_by_condition(
        filter_condition=AFTokenDepositsTransactions.wallet_address == bytes_wallet_address
    )

    return count


def get_deposit_chain_list(wallet_address):
    wallet_address = wallet_address.lower()
    bytes_wallet_address = bytes.fromhex(wallet_address[2:])

    chain_list = (
        db.session.query(AFTokenDepositsTransactions.wallet_address, AFTokenDepositsTransactions.chain_id)
        .filter(AFTokenDepositsTransactions.wallet_address == bytes_wallet_address)
        .group_by(AFTokenDepositsTransactions.wallet_address, AFTokenDepositsTransactions.chain_id)
        .all()
    )

    return chain_list


def get_deposit_assets_list(wallet_address):
    entities = build_entities(
        AFTokenDepositsCurrent, ["wallet_address", "chain_id", "contract_address", "token_address", "value"]
    )

    wallet_address = wallet_address.lower()
    bytes_wallet_address = bytes.fromhex(wallet_address[2:])

    assets_list = (
        db.session.query(AFTokenDepositsCurrent)
        .with_entities(*entities)
        .filter(AFTokenDepositsCurrent.wallet_address == bytes_wallet_address)
        .all()
    )

    return assets_list
