import decimal
from datetime import date, datetime

from flask_restx import Resource
from flask_restx.namespace import Namespace

from common.models import db
from common.models.af_ens_address_current import ENSAddress
from common.models.af_ens_event import ENSMiddle
from common.models.af_ens_node_current import ENSRecord
from common.utils.config import get_config

app_config = get_config()


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

        all_records_rows = db.session.query(ENSRecord).filter(ENSRecord.address == address).all()

        primary_address_row = db.session.query(ENSAddress).filter(ENSAddress.address == address).first()

        if primary_address_row:
            primary_record = db.session.query(ENSRecord).filter(ENSRecord.name == primary_address_row.name).first()
            if primary_record:
                res["primary_name"] = primary_record.name
                res["first_set_primary_name"] = datetime_to_string(primary_record.registration)

        if all_records_rows:
            res["ens_owned"] = [record.name for record in all_records_rows]
            res["first_own_ens"] = datetime_to_string(min(record.registration for record in all_records_rows))

        resolved_records = db.session.query(ENSRecord).filter(ENSRecord.address == address).all()
        res["resolved_to_ens"] = [record.name for record in resolved_records]

        return res


@af_ens_namespace.route("/v1/aci/<address>/ens/detail")
class ExplorerUserOperationDetails(Resource):
    def get(self, address):
        res = {

        }
        if address:
            address = bytes.fromhex(address[2:])
        else:
            return res


        all_records_rows = db.session.query(ENSMiddle).filter(ENSMiddle.from_address == address).all()

        return [model_to_dict(a) for a in all_records_rows]


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
