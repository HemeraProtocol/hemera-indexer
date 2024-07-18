from sqlalchemy import and_, func, or_

from common.models import db
from common.models.erc1155_token_transfers import ERC1155TokenTransfers
from common.models.erc20_token_transfers import ERC20TokenTransfers
from common.models.erc721_token_transfers import ERC721TokenTransfers
from common.models.scheduled_metadata import ScheduledWalletCountMetadata, ScheduledTokenCountMetadata
from common.models.tokens import Tokens
from common.utils.config import get_config
from common.utils.db_utils import build_entities
from common.utils.exception_control import APIError
from common.utils.format_utils import as_dict
from socialscan_api.app.db_service.contracts import get_contracts_by_addresses
from socialscan_api.app.db_service.wallet_addresses import get_token_txn_cnt_by_address
from socialscan_api.app.utils.utils import get_total_row_count, fill_address_display_to_transactions

app_config = get_config()

token_type_table_dict = {
    "tokentxns": Tokens,
    "tokentxns-nft": Tokens,
    "tokentxns-nft1155": Tokens,
}

token_transfer_type_table_dict = {
    "tokentxns": ERC20TokenTransfers,
    "tokentxns-nft": ERC721TokenTransfers,
    "tokentxns-nft1155": ERC1155TokenTransfers,
}


def type_to_token_table(type):
    return token_type_table_dict[type]


def type_to_token_transfer_table(type):
    return token_transfer_type_table_dict[type]


def get_address_token_transfer_cnt(token_type, condition, address):
    # Get count last update timestamp
    last_timestamp = db.session.query(func.max(ScheduledWalletCountMetadata.last_data_timestamp)).scalar()

    # Get historical count
    result = get_token_txn_cnt_by_address(token_type, address)

    new_transfer_count = (
        db.session.query(type_to_token_transfer_table(token_type))
        .filter(
            and_(
                (
                    type_to_token_transfer_table(token_type).block_timestamp >= last_timestamp.date()
                    if last_timestamp is not None
                    else True
                ),
                condition,
            )
        )
        .count()
    )
    return new_transfer_count + (result[0] if result and result[0] else 0)


def get_token_address_token_transfer_cnt(token_type, address):
    # Get count last update timestamp
    bytes_address = bytes.fromhex(address[2:])
    last_timestamp = db.session.query(func.max(ScheduledTokenCountMetadata.last_data_timestamp)).scalar()

    # Get historical count
    result = (
        db.session.query(type_to_token_table(token_type))
        .with_entities(type_to_token_table(token_type).transfer_count)
        .filter(type_to_token_table(token_type).address == bytes_address)
        .first()
    )
    return (
        db.session.query(type_to_token_transfer_table(token_type))
        .filter(
            and_(
                (
                    type_to_token_transfer_table(token_type).block_timestamp >= last_timestamp.date()
                    if last_timestamp is not None
                    else True
                ),
                type_to_token_transfer_table(token_type).token_address == bytes_address,
            )
        )
        .count()

    ) + (result[0] if result and result[0] else 0)


def get_raw_token_transfers(type, condition, page_index, page_size, is_count=True):
    if type not in token_transfer_type_table_dict:
        raise APIError("Invalid type", code=400)

    if type == "tokentxns":
        token_transfers = (
            db.session.execute(
                db.select(ERC20TokenTransfers)
                .where(condition)
                .order_by(
                    ERC20TokenTransfers.block_number.desc(),
                    ERC20TokenTransfers.log_index.desc(),
                )
                .limit(page_size)
                .offset((page_index - 1) * page_size)
            )
            .scalars()
            .all()
        )
    elif type == "tokentxns-nft":
        token_transfers = (
            db.session.query(ERC721TokenTransfers)
            .filter(condition)
            .order_by(
                ERC721TokenTransfers.block_number.desc(),
                ERC721TokenTransfers.log_index.desc(),
            )
            .limit(page_size)
            .offset((page_index - 1) * page_size)
            .all()
        )
    elif type == "tokentxns-nft1155":
        token_transfers = (
            db.session.query(ERC1155TokenTransfers)
            .filter(condition)
            .order_by(
                ERC1155TokenTransfers.block_number.desc(),
                ERC1155TokenTransfers.log_index.desc(),
                ERC1155TokenTransfers.token_id.desc(),
            )
            .limit(page_size)
            .offset((page_index - 1) * page_size)
            .all()
        )
    else:
        ##
        token_transfers = []

    if is_count:
        if (len(token_transfers) > 0 or page_index == 1) and len(token_transfers) < page_size:
            total_count = (page_index - 1) * page_size + len(token_transfers)
        elif condition:
            total_count = get_total_row_count(type_to_token_transfer_table(type).__tablename__)
        else:
            total_count = db.session.query(type_to_token_transfer_table(type)).filter(condition).count()
    else:
        total_count = 0

    return token_transfers, total_count


def parse_token_transfers(type, token_transfers):
    address_list = []
    token_address_list = []
    for token_transfer in token_transfers:
        token_address_list.append(token_transfer.token_address)
        address_list.append(token_transfer.from_address)
        address_list.append(token_transfer.to_address)
    token_address_list = list(set(token_address_list))
    address_list = list(set(address_list))

    # Find token
    if type == "tokentxns":
        tokens = db.session.query(Tokens).filter(
            and_(Tokens.address.in_(token_address_list), Tokens.token_type == 'ERC20')).all()
    elif type == "tokentxns-nft":
        tokens = db.session.query(Tokens).filter(
            and_(Tokens.address.in_(token_address_list), Tokens.token_type == 'ERC721')).all()
    elif type == "tokentxns-nft1155":
        tokens = db.session.query(Tokens).filter(
            and_(Tokens.address.in_(token_address_list), Tokens.token_type == 'ERC1155')).all()
    token_map = {}
    for token in tokens:
        token_map[token.address] = token

    # Find contract
    contracts = get_contracts_by_addresses(address_list=address_list, columns=['address'])
    contract_list = set(map(lambda x: x.address, contracts))

    token_transfer_list = []
    for token_transfer in token_transfers:
        token_transfer_json = as_dict(token_transfer)
        token = token_map.get(token_transfer.token_address)

        if type == "tokentxns":
            decimals = 18
            if token:
                decimals = token.decimals
            token_transfer_json["value"] = (
                "{0:.15f}".format(token_transfer.value / 10 ** decimals).rstrip("0").rstrip(".")
            )
        elif type == "tokentxns-nft":
            token_transfer_json["token_id"] = "{:f}".format(token_transfer.token_id)
        elif type == "tokentxns-nft1155":
            token_transfer_json["value"] = "{:f}".format(token_transfer.value)
            token_transfer_json["token_id"] = "{:f}".format(token_transfer.token_id)

        if token:
            token_transfer_json["token_symbol"] = token.symbol or "UNKNOWN"
            token_transfer_json["token_name"] = token.name or "Unknown Token"
            if type == "tokentxns" and token.icon_url:
                token_transfer_json["token_logo_url"] = token.icon_url
            else:
                token_transfer_json["token_logo_url"] = f"/images/empty-token-{app_config.chain}.png"
        else:
            token_transfer_json["token_symbol"] = "UNKNOWN"
            token_transfer_json["token_name"] = "Unknown Token"
            token_transfer_json["token_logo_url"] = f"/images/empty-token-{app_config.chain}.png"

        token_transfer_json["to_address_is_contract"] = token_transfer_json["to_address"] in contract_list
        token_transfer_json["from_address_is_contract"] = token_transfer_json["from_address"] in contract_list

        token_transfer_list.append(token_transfer_json)

    fill_address_display_to_transactions(token_transfer_list, ["0x" + address.hex() for address in address_list])
    return token_transfer_list


def get_token_by_address(address, columns='*'):
    bytes_address = bytes.fromhex(address[2:])
    entities = build_entities(Tokens, columns)

    tokens = (db.session.query(Tokens)
              .with_entities(*entities)
              .filter(Tokens.address == bytes_address)
              .first())

    return tokens


def get_tokens_cnt_by_condition(columns='*', filter_condition=None):
    entities = build_entities(Tokens, columns)

    count = (
        db.session.query(Tokens)
        .with_entities(entities)
        .filter(filter_condition)
        .count()
    )

    return count


def get_tokens_by_condition(columns='*', filter_condition=None, order=None, limit=1, offset=0):
    entities = build_entities(Tokens, columns)

    statement = db.session.query(Tokens).with_entities(*entities)

    if filter_condition is not None:
        statement = statement.filter(filter_condition)

    if order is not None:
        statement = statement.order_by(order)

    tokens = statement.limit(limit).offset(offset).all()

    return tokens


def get_token_transfers_with_token_by_hash(hash, model, transfer_columns='*', token_columns='*'):
    hash = bytes.fromhex(hash.lower()[2:])

    transfer_entities = build_entities(model, transfer_columns)
    token_entities = build_entities(Tokens, token_columns)

    token_transfers = (
        db.session.query(model)
        .with_entities(*transfer_entities)
        .filter(model.transaction_hash == hash)
        .join(
            Tokens,
            model.token_address == Tokens.address,
        )
        .add_columns(*token_entities)
        .all()
    )

    return token_transfers


def get_token_holders(token_address, model, columns='*', limit=None, offset=None):
    bytes_address = bytes.fromhex(token_address[2:])
    entities = build_entities(model, columns)

    statement = (
        db.session.query(model)
        .with_entities(*entities)
        .filter(
            model.token_address == bytes_address,
            model.balance_of > 0,
        )
        .order_by(model.balance_of.desc())
    )

    if limit:
        statement = statement.limit(limit)

    if offset:
        statement = statement.offset(offset)

    top_holders = statement.all()

    return top_holders


def get_token_holders_cnt(token_address, model, columns='*'):
    bytes_address = bytes.fromhex(token_address[2:])
    entities = build_entities(model, columns)

    holders_count = (
        db.session.query(model)
        .with_entities(*entities)
        .filter(
            model.token_address == bytes_address,
            model.balance_of > 0,
        )
        .count()
    )

    return holders_count

