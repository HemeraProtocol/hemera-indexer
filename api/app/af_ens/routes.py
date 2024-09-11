import decimal
from datetime import date, datetime

from flask_restx import Resource
from flask_restx.namespace import Namespace
from web3 import Web3

from common.models import db
from common.models.current_token_balances import CurrentTokenBalances
from common.models.erc721_token_id_changes import ERC721TokenIdChanges
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
            "first_register_time": None,
            "first_set_primary_name": None,
        }
        if address:
            address = bytes.fromhex(address[2:])
        else:
            return res

        dn = datetime.now()
        # current_address holds 721 & 1155 tokens
        all_721_owns = db.session.query(ERC721TokenIdChanges).filter(ERC721TokenIdChanges.token_owner == address).all()
        all_721_ids = [r.token_id for r in all_721_owns]
        all_owned = (
            db.session.query(ENSRecord).filter(and_(ENSRecord.token_id.in_(all_721_ids), ENSRecord.expires >= dn)).all()
        )
        res["ens_holdings"] = [r.name for r in all_owned if r.name and r.name.endswith(".eth")]
        all_1155_owns = db.session.query(CurrentTokenBalances).filter(CurrentTokenBalances.address == address).all()
        all_1155_ids = [r.token_id for r in all_1155_owns]
        all_owned_1155_ens = (
            db.session.query(ENSRecord)
            .filter(and_(ENSRecord.expires >= dn, ENSRecord.w_token_id.in_(all_1155_ids)))
            .all()
        )
        res["ens_holdings"].extend([r.name for r in all_owned_1155_ens if r.name and r.name.endswith(".eth")])
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
            .filter(and_(ENSMiddle.from_address == address, ENSMiddle.event_name == "NameRegistered"))
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
        node_name_map = {}
        for r in all_records_rows:
            if r.name:
                if r.name.endswith(".eth"):
                    node_name_map[r.node] = r.name
                else:
                    node_name_map[r.node] = r.name + ".eth"
        for r in all_records_rows:
            lis.append(
                {
                    "method": r.method,
                    "event": r.event_name,
                    "block_number": r.block_number,
                    "block_timestamp": datetime_to_string(r.block_timestamp),
                    "transaction_index": r.transaction_index,
                    "log_index": r.log_index,
                    "transaction_hash": "0x" + r.transaction_hash.hex(),
                    "node": "0x" + r.node.hex(),
                    "name": node_name_map.get(r.node),
                }
            )

        return lis


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
