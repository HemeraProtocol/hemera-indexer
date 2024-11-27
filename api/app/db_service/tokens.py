from sqlalchemy import and_, func, select

from api.app.db_service.wallet_addresses import get_token_txn_cnt_by_address
from api.app.utils.fill_info import fill_address_display_to_transactions, fill_is_contract_to_transactions
from common.models import db
from common.models.erc20_token_transfers import ERC20TokenTransfers
from common.models.erc721_token_transfers import ERC721TokenTransfers
from common.models.erc1155_token_transfers import ERC1155TokenTransfers
from common.models.scheduled_metadata import ScheduledMetadata
from common.models.token_prices import TokenPrices
from common.models.tokens import Tokens
from common.utils.config import get_config
from common.utils.db_utils import build_entities, get_total_row_count
from common.utils.exception_control import APIError
from common.utils.format_utils import as_dict, hex_str_to_bytes

app_config = get_config()

token_transfer_type_table_dict = {
    "tokentxns": ERC20TokenTransfers,
    "tokentxns-nft": ERC721TokenTransfers,
    "tokentxns-nft1155": ERC1155TokenTransfers,
    "erc20": ERC20TokenTransfers,
    "erc721": ERC721TokenTransfers,
    "erc1155": ERC1155TokenTransfers,
    "ERC20": ERC20TokenTransfers,
    "ERC721": ERC721TokenTransfers,
    "ERC1155": ERC1155TokenTransfers,
}


def type_to_token_transfer_table(type):
    return token_transfer_type_table_dict[type]


def get_address_token_transfer_cnt(token_type, condition, address):
    # Get count last update timestamp
    last_timestamp = db.session.query(func.max(ScheduledMetadata.last_data_timestamp)).scalar()

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


def get_token_address_token_transfer_cnt(token_type: str, address: str):
    # Get count last update timestamp
    bytes_address = hex_str_to_bytes(address)
    last_timestamp = db.session.query(func.max(ScheduledMetadata.last_data_timestamp)).scalar()

    # Get historical count
    result = (
        db.session.query(Tokens).with_entities(Tokens.transfer_count).filter(Tokens.address == bytes_address).first()
    )
    if result and result[0]:
        return result[0]
    return (
        db.session.query(type_to_token_transfer_table(token_type))
        .filter(
            and_(
                (
                    type_to_token_transfer_table(token_type).block_timestamp >= last_timestamp
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

    token_trasfer_table = token_transfer_type_table_dict[type]

    if type in ["tokentxns", "erc20", "ERC20", "tokentxns-nft", "erc721", "ERC721"]:
        token_transfers = (
            db.session.execute(
                db.select(token_trasfer_table)
                .where(condition)
                .order_by(
                    token_trasfer_table.block_timestamp.desc(),
                    token_trasfer_table.block_number.desc(),
                    token_trasfer_table.log_index.desc(),
                )
                .limit(page_size)
                .offset((page_index - 1) * page_size)
            )
            .scalars()
            .all()
        )
    elif type in ["tokentxns-nft1155", "erc1155", "ERC1155"]:
        token_transfers = (
            db.session.query(token_trasfer_table)
            .filter(condition)
            .order_by(
                token_trasfer_table.block_number.desc(),
                token_trasfer_table.log_index.desc(),
                token_trasfer_table.token_id.desc(),
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
            total_count = get_total_row_count(token_trasfer_table.__tablename__)
        else:
            total_count = db.session.query(token_trasfer_table).filter(condition).count()
    else:
        total_count = 0

    return token_transfers, total_count


def parse_token_transfers(token_transfers, type=None):
    bytea_address_list = []
    bytea_token_address_list = []
    for token_transfer in token_transfers:
        bytea_token_address_list.append(token_transfer.token_address)
        bytea_address_list.append(token_transfer.from_address)
        bytea_address_list.append(token_transfer.to_address)
    bytea_token_address_list = list(set(bytea_token_address_list))
    bytea_address_list = list(set(bytea_address_list))

    # Find token
    if type in ["tokentxns", "erc20", "ERC20"]:
        tokens = (
            db.session.query(Tokens)
            .filter(and_(Tokens.address.in_(bytea_token_address_list), Tokens.token_type == "ERC20"))
            .all()
        )
    elif type in ["tokentxns-nft", "erc721", "ERC721"]:
        tokens = (
            db.session.query(Tokens)
            .filter(and_(Tokens.address.in_(bytea_token_address_list), Tokens.token_type == "ERC721"))
            .all()
        )
    elif type in ["tokentxns-nft1155", "erc1155", "ERC1155"]:
        tokens = (
            db.session.query(Tokens)
            .filter(and_(Tokens.address.in_(bytea_token_address_list), Tokens.token_type == "ERC1155"))
            .all()
        )
    else:
        tokens = db.session.query(Tokens).filter(Tokens.address.in_(bytea_token_address_list)).all()
    token_map = {}  # bytea -> token
    for token in tokens:
        token_map[token.address] = token

    token_transfer_list = []
    for token_transfer in token_transfers:
        token_transfer_json = as_dict(token_transfer)
        token = token_map.get(token_transfer.token_address)

        if type in ["tokentxns", "erc20", "ERC20"]:
            decimals = 18
            if token:
                decimals = token.decimals
            token_transfer_json["value"] = (
                "{0:.15f}".format(token_transfer.value / 10**decimals).rstrip("0").rstrip(".")
            )
        elif type in ["tokentxns-nft", "erc721", "ERC721"]:
            token_transfer_json["token_id"] = "{:f}".format(token_transfer.token_id)
        elif type in ["tokentxns-nft1155", "erc1155", "ERC1155"]:
            token_transfer_json["value"] = "{:f}".format(token_transfer.value)
            token_transfer_json["token_id"] = "{:f}".format(token_transfer.token_id)

        if token:
            token_transfer_json["token_symbol"] = token.symbol or "UNKNOWN"
            token_transfer_json["token_name"] = token.name or "Unknown Token"
            token_transfer_json["token_logo_url"] = token.icon_url
        else:
            token_transfer_json["token_symbol"] = "UNKNOWN"
            token_transfer_json["token_name"] = "Unknown Token"
            token_transfer_json["token_logo_url"] = None

        token_transfer_list.append(token_transfer_json)

    fill_is_contract_to_transactions(token_transfer_list, bytea_address_list)
    fill_address_display_to_transactions(token_transfer_list, bytea_address_list)

    return token_transfer_list


def get_token_by_address(address: str, columns="*"):
    bytes_address = hex_str_to_bytes(address)
    entities = build_entities(Tokens, columns)

    tokens = db.session.query(Tokens).with_entities(*entities).filter(Tokens.address == bytes_address).first()

    return tokens


def get_tokens_cnt_by_condition(columns="*", filter_condition=None):
    entities = build_entities(Tokens, columns)

    statement = db.session.query(Tokens).with_entities(*entities)

    if filter_condition is not None:
        statement = statement.filter(filter_condition)

    count = statement.count()

    return count


def get_tokens_by_condition(columns="*", filter_condition=None, order=None, limit=1, offset=0):
    entities = build_entities(Tokens, columns)

    statement = db.session.query(Tokens).with_entities(*entities)

    if filter_condition is not None:
        statement = statement.filter(filter_condition)

    if order is not None:
        statement = statement.order_by(order)

    tokens = statement.limit(limit).offset(offset).all()

    return tokens


def get_token_transfers_with_token_by_hash(hash, model, transfer_columns="*", token_columns="*"):
    hash = hex_str_to_bytes(hash.lower())

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


def get_token_holders(token_address: str, model, columns="*", limit=None, offset=None):
    bytes_token_address = hex_str_to_bytes(token_address)
    entities = build_entities(model, columns)

    statement = (
        db.session.query(model)
        .with_entities(*entities)
        .filter(
            model.token_address == bytes_token_address,
            model.balance > 0,
        )
        .order_by(model.balance.desc())
    )

    if limit is not None:
        statement = statement.limit(limit)

    if offset is not None:
        statement = statement.offset(offset)

    top_holders = statement.all()

    return top_holders


def get_token_holders_cnt(token_address: str, model, columns="*"):
    bytes_token_address = hex_str_to_bytes(token_address)
    entities = build_entities(model, columns)

    holders_count = (
        db.session.query(model)
        .with_entities(*entities)
        .filter(
            model.token_address == bytes_token_address,
            model.balance > 0,
        )
        .count()
    )

    return holders_count


def get_token_price_map_by_symbol_list(token_symbol_list):
    token_price_map = {}
    for symbol in token_symbol_list:
        token_price = db.session.execute(
            select(TokenPrices).where(TokenPrices.symbol == symbol).order_by(TokenPrices.timestamp.desc()).limit(1)
        ).scalar()
        if token_price:
            token_price_map[symbol] = token_price.price
    return token_price_map
