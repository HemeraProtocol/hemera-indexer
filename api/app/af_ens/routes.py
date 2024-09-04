import decimal
from datetime import date, datetime

from flask_restx import Resource
from flask_restx.namespace import Namespace

from common.models import db
from common.models.af_ens_address_current import ENSAddress
from common.models.af_ens_event import ENSMiddle
from common.models.af_ens_node_current import ENSRecord
from common.models.erc721_token_id_changes import ERC721TokenIdChanges
from common.utils.config import get_config

app_config = get_config()
from sqlalchemy import or_, and_, desc, func


af_ens_namespace = Namespace("User Operation Namespace", path="/", description="ENS feature")


@af_ens_namespace.route("/v1/aci/<address>/ens/current")
class ExplorerUserOperationDetails(Resource):
    def get(self, address):
        res = {
            "primary_name": None,
            "be_resolved_by_ens": [],
            "first_set_primary_name": None,
            "ens_holdings": [],
            "first_register_time": None
        }
        if address:
            address = bytes.fromhex(address[2:])
        else:
            return res

        # current_address holds 721 & 1155 tokens
        all_721_owns = db.session.query(ERC721TokenIdChanges).filter(ERC721TokenIdChanges.token_owner == address).all()
        all_721_ids = [r.token_id for r in all_721_owns]
        all_owned = db.session.query(ENSRecord).filter(ENSRecord.token_id.in_(all_721_ids)).all()
        res['ens_holdings'] = [r.name for r in all_owned]
        # TODO support 1155
        # all_1155_owns = db.session.query(ENSRecord).filter(ENSRecord.address == address).all()

        primary_address_row = db.session.query(ENSAddress).filter(ENSAddress.address == address).first()
        if primary_address_row:
            primary_record = db.session.query(ENSRecord).filter(ENSRecord.name == primary_address_row.name).first()
            if primary_record:
                res["primary_name"] = primary_record.name

        be_resolved_ens = db.session.query(ENSAddress).filter(ENSAddress.address == address).all()
        res['be_resolved_by_ens'] = [r.name for r in be_resolved_ens]

        first_register = db.session.query(ENSMiddle).filter(and_(ENSMiddle.from_address == address, ENSMiddle.event_name == 'NameRegistered')).first()
        if first_register:
            res['first_register_time'] = datetime_to_string(first_register.block_timestamp)

        return res


@af_ens_namespace.route("/v1/aci/<address>/ens/detail")
class ExplorerUserOperationDetails(Resource):
    def get(self, address):
        lis = []
        if address:
            address = bytes.fromhex(address[2:])
        else:
            return lis

        all_records_rows = db.session.query(ENSMiddle).filter(ENSMiddle.from_address == address).order_by(ENSMiddle.block_number, ENSMiddle.transaction_index, ENSMiddle.log_index.desc()).all()
        all_ens_records = db.session.query(ENSRecord).filter(ENSRecord.node.in_([r.node for r in all_records_rows])).all()
        node_name_map = {r.node: r.name for r in all_ens_records if r.name}
        for r in all_records_rows:
            lis.append({
                'method': r.method,
                'event': r.event_name,
                'block_number': r.block_number,
                'transaction_index': r.transaction_index,
                'log_index': r.log_index,
                'transaction_hash': '0x' + r.transaction_hash.hex(),
                'node': '0x' + r.node.hex(),
                'name': node_name_map.get(r.node)
            })

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
            res[c.name] = '0x' + v.hex()
        elif isinstance(v, decimal.Decimal):
            res[c.name] = str(v)
        else:
            res[c.name] = v
    return res
