import decimal
from datetime import date, datetime

from flask_restx import Resource
from flask_restx.namespace import Namespace
from web3 import Web3

from api.app.af_ens.action_types import OperationType
from common.models import db
from common.models.current_token_balances import CurrentTokenBalances
from common.models.erc721_token_id_details import ERC721TokenIdDetails
from common.models.erc721_token_transfers import ERC721TokenTransfers
from common.models.erc1155_token_transfers import ERC1155TokenTransfers
from common.utils.config import get_config
from indexer.modules.custom.hemera_ens.models.af_ens_address_current import ENSAddress
from indexer.modules.custom.hemera_ens.models.af_ens_event import ENSMiddle
from indexer.modules.custom.hemera_ens.models.af_ens_node_current import ENSRecord

app_config = get_config()
from sqlalchemy import and_, or_

w3 = Web3(Web3.HTTPProvider("https://ethereum-rpc.publicnode.com"))
af_ens_namespace = Namespace("User Operation Namespace", path="/", description="ENS feature")


@af_ens_namespace.route("/v1/aci/<address>/ens/current")
class ExplorerUserOperationDetails(Resource):
    def get(self, address):
        res = {
            "primary_name": None,
            "be_resolved_by_ens": [],
            "ens_holdings": [],
            "ens_holdings_total": None,
            "first_register_time": None,
            "first_set_primary_name": None,
        }
        if address:
            address = bytes.fromhex(address[2:])
        else:
            return res

        dn = datetime.now()
        # current_address holds 721 & 1155 tokens
        ens_token_address = bytes.fromhex("57F1887A8BF19B14FC0DF6FD9B2ACC9AF147EA85")
        all_721_owns = (
            db.session.query(ERC721TokenIdDetails)
            .filter(
                and_(
                    ERC721TokenIdDetails.token_owner == address, ERC721TokenIdDetails.token_address == ens_token_address
                )
            )
            .all()
        )
        all_721_ids = [r.token_id for r in all_721_owns]
        all_owned = db.session.query(ENSRecord).filter(and_(ENSRecord.token_id.in_(all_721_ids))).all()
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
            .filter(
                and_(CurrentTokenBalances.address == address, CurrentTokenBalances.token_address == ens_1155_address)
            )
            .all()
        )
        all_1155_ids = [r.token_id for r in all_1155_owns]
        all_owned_1155_ens = (
            db.session.query(ENSRecord)
            .filter(and_(ENSRecord.expires >= dn, ENSRecord.w_token_id.in_(all_1155_ids)))
            .all()
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
            primary_record = db.session.query(ENSRecord).filter(ENSRecord.name == primary_address_row.name).first()
            if primary_record:
                res["primary_name"] = primary_record.name
        else:
            res["primary_name"] = w3.ens.name(w3.to_checksum_address(w3.to_hex(address)))

        be_resolved_ens = (
            db.session.query(ENSRecord).filter(and_(ENSRecord.address == address, ENSRecord.expires >= dn)).all()
        )
        res["be_resolved_by_ens"] = [r.name for r in be_resolved_ens if r.name and r.name.endswith(".eth")]

        first_register = (
            db.session.query(ENSMiddle)
            .filter(and_(ENSMiddle.from_address == address, or_(ENSMiddle.event_name == "NameRegistered", ENSMiddle.event_name == "HashRegistered")))
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
            .first()
        )
        if first_set_name:
            res["first_set_primary_name"] = datetime_to_string(first_set_name.block_timestamp)

        return res


@af_ens_namespace.route("/v1/aci/<address>/ens/detail")
class ExplorerUserOperationDetails(Resource):
    def get(self, address):
        lis = []
        if address:
            address = bytes.fromhex(address[2:])
        else:
            return lis

        all_records_rows = (
            db.session.query(ENSMiddle)
            .filter(ENSMiddle.from_address == address)
            .order_by(ENSMiddle.block_number, ENSMiddle.transaction_index, ENSMiddle.log_index.desc())
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
            if hasattr(r, "node") and r.node:
                name = node_name_map[r.node]
            elif hasattr(r, "token_id") and r.token_id:
                name = token_id_name_map[r.token_id]
            elif hasattr(r, "w_token_id") and r.w_token_id:
                name = token_id_name_map[r.w_token_id]
            base = {
                "block_number": r.block_number,
                "block_timestamp": datetime_to_string(r.block_timestamp),
                "transaction_hash": "0x" + r.transaction_hash.hex(),
                "name": name,
            }

            extras = get_action_type(r)
            base.update(extras)
            lis.append(base)

        return lis


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
            "from": "0x" + record.from_address.hex(),
            "to": "0x" + record.to_address.hex(),
            "token_id": int(record.token_id),
        }
    if record.method == "setName" or record.event_name == "NameChanged":
        return {"action_type": OperationType.SET_PRIMARY_NAME.value}
    if record.event_name == "NameRegistered" or record.event_name == "HashRegistered":
        return {"action_type": OperationType.REGISTER.value}
    if record.event_name == "NameRenewed":
        return {"action_type": OperationType.RENEW.value, "expires": datetime_to_string(record.expires)}
    if record.event_name == "AddressChanged":
        return {"action_type": OperationType.SET_RESOLVED_ADDRESS.value, "address": "0x" + record.address.hex()}
    raise ValueError("Unknown operation type")


def datetime_to_string(dt, format="%Y-%m-%d %H:%M:%S"):
    if isinstance(dt, datetime):
        return dt.strftime(format)
    elif isinstance(dt, date):
        return dt.strftime(format)
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
            res[c.name] = "0x" + v.hex()
        elif isinstance(v, decimal.Decimal):
            res[c.name] = str(v)
        else:
            res[c.name] = v
    return res
