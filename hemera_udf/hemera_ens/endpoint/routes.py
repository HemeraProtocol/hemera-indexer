import decimal
from copy import deepcopy
from datetime import date, datetime
from typing import Any, Dict, Optional

import flask
from flask import request
from flask_restx import Resource
from sqlalchemy.sql import and_, or_
from web3 import Web3

from hemera.api.app.address.features import register_feature
from hemera.api.app.cache import cache
from hemera.common.models import db
from hemera.common.models.current_token_balances import CurrentTokenBalances
from hemera.common.models.erc721_token_id_details import ERC721TokenIdDetails
from hemera.common.models.erc721_token_transfers import ERC721TokenTransfers
from hemera.common.models.erc1155_token_transfers import ERC1155TokenTransfers
from hemera.common.utils.config import get_config
from hemera.common.utils.exception_control import APIError
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from hemera.common.utils.web3_utils import ZERO_ADDRESS
from hemera_udf.hemera_ens.endpoint import af_ens_namespace
from hemera_udf.hemera_ens.endpoint.action_types import OperationType
from hemera_udf.hemera_ens.models.af_ens_address_current import ENSAddress
from hemera_udf.hemera_ens.models.af_ens_event import ENSMiddle
from hemera_udf.hemera_ens.models.af_ens_node_current import ENSRecord

app_config = get_config()

w3 = Web3(Web3.HTTPProvider("https://ethereum-rpc.publicnode.com"))

PAGE_SIZE = 10


@register_feature("ens", "value")
def get_ens_current(address) -> Optional[Dict[str, Any]]:
    if isinstance(address, str):
        address = hex_str_to_bytes(address)

    res = {
        "primary_name": None,
        "resolve_to_names": [],
        "ens_holdings": [],
        "ens_holdings_total": 0,
        "first_register_time": None,
        "first_set_primary_time": None,
        "resolve_to_names_total": 0,
    }
    origin_res = deepcopy(res)

    dn = datetime.now()
    # current_address holds 721 & 1155 tokens
    ens_token_address = bytes.fromhex("57F1887A8BF19B14FC0DF6FD9B2ACC9AF147EA85")
    all_721_owns = (
        db.session.query(ERC721TokenIdDetails)
        .filter(
            and_(ERC721TokenIdDetails.token_owner == address, ERC721TokenIdDetails.token_address == ens_token_address)
        )
        .all()
    )
    all_721_ids = [r.token_id for r in all_721_owns]
    all_owned = (
        db.session.query(ENSRecord)
        .filter(and_(ENSRecord.token_id.in_(all_721_ids), ENSRecord.w_token_id.is_(None)))
        .all()
    )
    all_owned_map = {r.token_id: r for r in all_owned}
    for id in all_721_ids:
        r = all_owned_map.get(id)
        res["ens_holdings"].append(
            {
                "name": r.name if r else None,
                "is_expire": r.expires < dn if r and r.expires else True,
                "type": "ERC721",
                "token_id": str(id),
            }
        )
    ens_1155_address = bytes.fromhex("d4416b13d2b3a9abae7acd5d6c2bbdbe25686401")
    all_1155_owns = (
        db.session.query(CurrentTokenBalances)
        .filter(and_(CurrentTokenBalances.address == address, CurrentTokenBalances.token_address == ens_1155_address))
        .all()
    )
    all_1155_ids = [r.token_id for r in all_1155_owns]
    all_owned_1155_ens = (
        db.session.query(ENSRecord).filter(and_(ENSRecord.expires >= dn, ENSRecord.w_token_id.in_(all_1155_ids))).all()
    )
    res["ens_holdings"].extend(
        [
            {"name": r.name, "is_expire": r.expires < dn, "type": "ERC1155", "token_id": str(r.w_token_id)}
            for r in all_owned_1155_ens
            if r.name and r.name.endswith(".eth")
        ]
    )
    res["ens_holdings_total"] = len(res["ens_holdings"])
    primary_address_row = db.session.query(ENSAddress).filter(ENSAddress.address == address).first()
    if primary_address_row:
        res["primary_name"] = primary_address_row.name
    # else:
    #    res["primary_name"] = w3.ens.name(w3.to_checksum_address(w3.to_hex(address)))

    be_resolved_ens = db.session.query(ENSRecord).filter(and_(ENSRecord.address == address)).all()
    res["resolve_to_names"] = [
        {
            "name": r.name,
            "is_expire": r.expires < dn if r and r.expires else True,
        }
        for r in be_resolved_ens
        if r.name and r.name.endswith(".eth")
    ]
    res["resolve_to_names_total"] = len(res["resolve_to_names"])

    first_register = (
        db.session.query(ENSMiddle)
        .filter(
            and_(
                ENSMiddle.from_address == address,
                or_(ENSMiddle.event_name == "NameRegistered", ENSMiddle.event_name == "HashRegistered"),
            )
        )
        .order_by(ENSMiddle.block_number)
        .first()
    )
    if first_register:
        res["first_register_time"] = datetime_to_string(first_register.block_timestamp)
    first_set_name = (
        db.session.query(ENSMiddle)
        .filter(
            and_(
                ENSMiddle.from_address == address,
                or_(ENSMiddle.method == "setName", ENSMiddle.event_name == "NameChanged"),
            )
        )
        .order_by(ENSMiddle.block_number)
        .first()
    )
    if first_set_name:
        res["first_set_primary_time"] = datetime_to_string(first_set_name.block_timestamp)

    return res if res != origin_res else None


@register_feature("ens", "events")
def get_ens_events(address, limit=5, offset=0) -> Optional[Dict[str, Any]]:
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    events = []
    all_records_rows = (
        db.session.query(ENSMiddle)
        .filter(ENSMiddle.from_address == address)
        .order_by(ENSMiddle.block_number.desc(), ENSMiddle.log_index.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    # erc721_ids = list({r.token_id for r in all_records_rows if r.token_id})
    # erc721_id_transfers = (
    #     db.session.query(ERC721TokenTransfers)
    #     .filter(ERC721TokenTransfers.token_id.in_(erc721_ids))
    #     .order_by(ERC721TokenTransfers.block_number)
    #     .all()
    # )
    #
    # erc1155_ids = list({r.w_token_id for r in all_records_rows if r.w_token_id})
    # erc1155_id_transfers = (
    #     db.session.query(ERC1155TokenTransfers)
    #     .filter(ERC1155TokenTransfers.token_id.in_(erc1155_ids))
    #     .order_by(ERC1155TokenTransfers.block_number)
    #     .all()
    # )

    node_name_map = {}
    for r in all_records_rows:
        if r.name:
            if r.name.endswith(".eth"):
                node_name_map[r.node] = r.name
            else:
                node_name_map[r.node] = r.name + ".eth"
    token_id_name_map = dict()
    for r in all_records_rows:
        if r.token_id:
            token_id_name_map[r.token_id] = node_name_map[r.node]
        if r.w_token_id:
            token_id_name_map[r.w_token_id] = node_name_map[r.node]

    all_rows = merge_ens_middle(all_records_rows)

    for r in all_rows:
        name = None
        if hasattr(r, "node") and r.node and r.node in node_name_map:
            name = node_name_map[r.node]
        elif hasattr(r, "token_id") and r.token_id and r.token_id in token_id_name_map:
            name = token_id_name_map[r.token_id]
        elif hasattr(r, "w_token_id") and r.w_token_id and r.w_token_id in token_id_name_map:
            name = token_id_name_map[r.w_token_id]
        base = {
            "block_number": r.block_number,
            "block_timestamp": datetime_to_string(r.block_timestamp),
            "transaction_hash": bytes_to_hex_str(r.transaction_hash),
            "name": name,
        }

        extras = get_action_type(r)
        base.update(extras)
        events.append(base)

    if len(events) == 0:
        return None

    return {"data": events, "total": len(events)}


@af_ens_namespace.route("/v1/aci/<address>/ens/current")
class ACIEnsCurrent(Resource):
    def get(self, address):
        try:
            address = hex_str_to_bytes(address)
        except Exception:
            raise APIError("Invalid Address Format", code=400)
        return get_ens_current(address)


@af_ens_namespace.route("/v1/aci/<address>/ens/detail")
class ACIEnsDetail(Resource):
    def get(self, address):
        try:
            address = hex_str_to_bytes(address)
        except Exception:
            raise APIError("Invalid Address Format", code=400)

        page_index = int(flask.request.args.get("page", 1))
        page_size = int(flask.request.args.get("size", PAGE_SIZE))
        limit = page_size
        offset = (page_index - 1) * page_size
        return get_ens_events(address, limit, offset) or {"data": [], "total": 0} | {
            "page": page_index,
            "size": page_size,
        }


def merge_ens_middle(records):
    """Merge consecutive records when setAddr and nameRegistered are duplicated"""
    if not records:
        return []

    res = [records[0]]

    for current_record in records[1:]:
        previous_record = res[-1]

        # Check if the current record should be merged with the previous one
        if (
            current_record.event_name == previous_record.event_name == "AddressChanged"
            and current_record.name == previous_record.name
        ) or (
            current_record.event_name == previous_record.event_name == "NameRegistered"
            and current_record.name == previous_record.name
        ):
            for column in ENSMiddle.__table__.columns:
                current_value = getattr(current_record, column.name)
                previous_value = getattr(previous_record, column.name)
                if previous_value is None and current_value is not None:
                    setattr(previous_record, column.name, current_value)
        else:
            res.append(current_record)

    return res


def get_action_type(record):
    if isinstance(record, ERC721TokenTransfers) or isinstance(record, ERC1155TokenTransfers):
        return {
            "action_type": OperationType.TRANSFER.value,
            "from": bytes_to_hex_str(record.from_address),
            "to": bytes_to_hex_str(record.to_address),
            "token_id": int(record.token_id),
        }
    if record.method == "setName" or record.event_name == "NameChanged":
        return {"action_type": OperationType.SET_PRIMARY_NAME.value}
    if record.event_name == "NameRegistered" or record.event_name == "HashRegistered":
        return {"action_type": OperationType.REGISTER.value}
    if record.event_name == "NameRenewed":
        return {"action_type": OperationType.RENEW.value, "expires": datetime_to_string(record.expires)}
    if record.event_name == "AddressChanged":
        return {"action_type": OperationType.SET_RESOLVED_ADDRESS.value, "address": bytes_to_hex_str(record.address)}
    raise ValueError("Unknown operation type")


def datetime_to_string(dt, format="%Y-%m-%d %H:%M:%S"):
    if isinstance(dt, datetime):
        return dt.astimezone().isoformat("T", "seconds")
    elif isinstance(dt, date):
        return dt.astimezone().isoformat("T", "seconds")
    elif dt is None:
        return None
    else:
        raise ValueError(f"Unsupported type for dt: {type(dt)}. Expected datetime or date.")


def model_to_dict(instance):
    res = {}
    for c in instance.__table__.columns:
        v = getattr(instance, c.name)
        if isinstance(v, datetime):
            res[c.name] = v.isoformat()
        elif isinstance(v, bytes):
            res[c.name] = bytes_to_hex_str(v)
        elif isinstance(v, decimal.Decimal):
            res[c.name] = str(v)
        else:
            res[c.name] = v
    return res


def make_key(self):
    path = request.path
    address_or_names = request.get_json().get("address")
    if not address_or_names:
        address_or_names = request.get_json().get("name")
    if not address_or_names:
        return ""
    address_or_names.sort()
    args = str(hash(frozenset(address_or_names)))
    # return (path + args).encode('utf-8')
    return path + args


@af_ens_namespace.route("/v1/ens/address/<address>")
class ACIEnsAddress(Resource):
    @cache.cached(timeout=360)
    def get(self, address):
        address = address.lower()
        if address == ZERO_ADDRESS:
            return {}

        current_time = datetime.utcnow()

        result = (
            db.session.query(ENSRecord.name)
            .join(ENSAddress, (ENSAddress.name == ENSRecord.name) & (ENSRecord.address == ENSAddress.address))
            .filter(ENSAddress.address == hex_str_to_bytes(address), ENSRecord.expires >= current_time)
            .one_or_none()
        )

        return {address: result[0]} if result else {}


@af_ens_namespace.route("/v1/ens/name/<name>")
class ACIEnsName(Resource):
    @cache.cached(timeout=360)
    def get(self, name):
        current_time = datetime.utcnow()

        result = (
            db.session.query(ENSRecord.address)
            .filter(
                ENSRecord.name == name,
                ENSRecord.expires >= current_time,
                ENSRecord.address != hex_str_to_bytes(ZERO_ADDRESS),
            )
            .one_or_none()
        )

        return {name: bytes_to_hex_str(result[0])} if result else {}


@af_ens_namespace.route("/v1/ens/batch/name")
class ACIEnsBatchName(Resource):
    @cache.cached(timeout=360, make_cache_key=make_key)
    def post(self):
        current_time = datetime.utcnow()
        request_data = request.get_json()
        names = list(set(request_data.get("name", [])))  # 去重

        if not names:
            return {}

        if len(names) > 50:
            return {"error": "Too many names, should be less than 50"}

        results = (
            db.session.query(ENSRecord.name, ENSRecord.address)
            .filter(
                ENSRecord.name.in_(names),
                ENSRecord.expires >= current_time,
                ENSRecord.address != hex_str_to_bytes(ZERO_ADDRESS),
            )
            .all()
        )

        return {name: bytes_to_hex_str(address) for name, address in results}


@af_ens_namespace.route("/v1/ens/batch/address")
class ACIEnsBatchAddress(Resource):
    @cache.cached(timeout=360, make_cache_key=make_key)
    def post(self):
        current_time = datetime.utcnow()
        request_data = request.get_json()
        address_s = request_data.get("address", [])

        addresses = list(set(hex_str_to_bytes(ad.lower()) for ad in address_s if ad))

        if not addresses:
            return {}

        if len(addresses) > 50:
            return {"error": "Too many addresses, should be less than 50"}

        results = (
            db.session.query(ENSAddress.address, ENSRecord.name)
            .join(ENSRecord, (ENSAddress.name == ENSRecord.name) & (ENSRecord.address == ENSAddress.address))
            .filter(ENSAddress.address.in_(addresses), ENSRecord.expires >= current_time)
            .all()
        )
        return {bytes_to_hex_str(address): name for address, name in results}
