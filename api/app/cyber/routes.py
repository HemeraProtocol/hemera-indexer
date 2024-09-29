from flask import request
from flask_restx import Namespace, Resource

from api.app.cache import cache
from common.models import db
from indexer.modules.custom.cyber_id.models.cyber_models import CyberAddress

cyber_namespace = Namespace("Cyber Namespace", path="/", description="cyber api")


@cyber_namespace.route("/v1/cyber/address/name")
class CyberAddressName(Resource):
    @cache.cached(timeout=60, query_string=True)
    def get(self):
        addresses = request.args.get("address", "").split(",")
        addresses = [bytes.fromhex(address.lower()[2:]) for address in addresses]
        cyber_addresses = db.session.query(CyberAddress).filter(CyberAddress.address.in_(addresses)).all()
        res = {}
        for cyber_address in cyber_addresses:
            res[cyber_address.address.hex()] = cyber_address.name
        return {"data": res}, 200
