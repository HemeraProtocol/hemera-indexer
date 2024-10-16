#!/usr/bin/env python

"""api endpoints"""
import decimal
from datetime import datetime

from flask_restx import Resource
from flask_restx.namespace import Namespace
from sqlalchemy.sql import and_

from common.models import db
from common.utils.config import get_config
from common.utils.exception_control import APIError
from indexer.modules.custom.a_demo.models.af_sample_address_current import SampleAddressCurrent
from indexer.modules.custom.a_demo.models.af_sample_event import SampleEvent

app_config = get_config()

af_sample_namespace = Namespace("User Operation Namespace", path="/", description="Sample feature")


PAGE_SIZE = 10


@af_sample_namespace.route("/v1/aci/<address>/sample/current")
class ACIEnsCurrent(Resource):
    def get(self, address):
        if address:
            address = bytes.fromhex(address[2:])
        else:
            raise APIError("Invalid Address Format", code=400)

        record = db.session.query(SampleAddressCurrent).filter(and_(SampleAddressCurrent.address == address)).first()
        return model_to_dict(record)


@af_sample_namespace.route("/v1/aci/<address>/sample/detail")
class ACIEnsDetail(Resource):
    def get(self, address):
        if address:
            address = bytes.fromhex(address[2:])
        else:
            raise APIError("Invalid Address Format", code=400)

        all_records_rows = (
            db.session.query(SampleEvent)
            .filter(SampleEvent.from_address == address)
            .order_by(SampleEvent.block_number.desc(), SampleEvent.log_index.desc())
            .limit(PAGE_SIZE)
            .all()
        )
        events = [model_to_dict(a) for a in all_records_rows]

        return {
            "data": events,
            "total": len(events),
            "page": 1,
            "size": PAGE_SIZE,
        }


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
