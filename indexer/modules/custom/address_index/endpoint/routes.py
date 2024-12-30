from datetime import datetime

import flask
from flask_restx import Resource

from api.app.cache import cache
from common.utils.format_utils import format_to_dict
from indexer.modules.custom.address_index import address_profile_namespace
from indexer.modules.custom.address_index.schemas.api import (
    aci_score_response_model,
    address_base_info_model,
    address_base_info_response_model,
    address_developer_info_response_model,
    validate_eth_address,
)
from indexer.modules.custom.address_index.utils.helpers import (
    get_address_assets,
    get_address_base_info,
    get_address_developer_info,
    get_all_udf_dashboards,
    get_all_udf_dashboards_data,
    get_contract_deployed_events,
    get_contract_deployer_profile,
    get_daily_active_address,
    get_wallet_address_volumes,
)
from indexer.modules.custom.address_index.utils.score import calculate_aci_score

PAGE_SIZE = 10
MAX_TRANSACTION = 500000
MAX_TRANSACTION_WITH_CONDITION = 10000
MAX_INTERNAL_TRANSACTION = 10000
MAX_TOKEN_TRANSFER = 10000


@address_profile_namespace.route("/v1/aci/<address>/base_info")
class ACIProfiles(Resource):
    @validate_eth_address
    @address_profile_namespace.marshal_with(address_base_info_response_model)
    @cache.cached(timeout=60)
    def get(self, address):
        profile = get_address_base_info(address) | {"address": address.lower()}

        return {"code": 200, "message": "OK", "data": profile}


@address_profile_namespace.route("/v1/aci/<address>/developer_info")
class ACIDeveloperProfiles(Resource):
    @validate_eth_address
    @address_profile_namespace.marshal_with(address_developer_info_response_model)
    @cache.cached(timeout=60)
    def get(self, address):
        profile = get_address_developer_info(address) | {"address": address.lower()}

        if profile.get("first_contract_deployed_block_timestamp"):
            delta = datetime.utcnow() - profile["first_contract_deployed_block_timestamp"]
            years = delta.days / 365
            profile["years_since_first_contract"] = round(years, 1)
        else:
            profile["years_since_first_contract"] = 0.0

        return {"code": 200, "message": "OK", "data": profile}


@address_profile_namespace.route("/v1/aci/<address>/profile")
class ACIProfiles(Resource):
    @validate_eth_address
    @address_profile_namespace.marshal_with(aci_score_response_model)
    @cache.cached(timeout=60)
    def get(self, address):
        # 1. Check transaction count
        # 2. Calculate total gas spent
        # 3. Get first transaction timestamp
        profile = get_address_base_info(address)

        # 4. Calculate TVL
        assets = get_address_assets(address)

        # 5. Calculate Volume
        volumes = get_wallet_address_volumes(address)

        score = calculate_aci_score(profile, assets, volumes)
        res = {
            "score": score,
            "base_info": profile,
            "assets": assets,
            "volumes": volumes,
        }
        res = format_to_dict(res)

        return {"code": 200, "message": "OK", "data": res}


@address_profile_namespace.route("/v1/aci/<address>/assets")
class ACIAssets(Resource):
    @validate_eth_address
    def get(self, address):
        asset = get_address_assets(address)
        return {
            "code": 200,
            "message": "OK",
            "data": asset,
        }


@address_profile_namespace.route("/v1/aci/<address>/contract_deployer/profile")
class ACIContractDeployerProfile(Resource):
    @validate_eth_address
    def get(self, address):
        return get_contract_deployer_profile(address) or {"deployed_countract_count": 0, "first_deployed_time": None}


@address_profile_namespace.route("/v1/aci/<address>/contract_deployer/events")
class ACIContractDeployerEvents(Resource):
    @validate_eth_address
    def get(self, address):
        page_index = int(flask.request.args.get("page", 1))
        page_size = int(flask.request.args.get("size", PAGE_SIZE))
        limit = page_size
        offset = (page_index - 1) * page_size

        return (get_contract_deployed_events(address, limit=limit, offset=offset) or {"data": [], "total": 0}) | {
            "size": page_size,
            "page": page_index,
        }


@address_profile_namespace.route("/v1/aci/<address>/volumes")
class ACIVolumes(Resource):
    @validate_eth_address
    @cache.cached(timeout=360, query_string=True)
    def get(self, address):
        address_bytes = bytes.fromhex(address[2:])


@address_profile_namespace.route("/v1/aci/udf_dashboards")
class UDFDashboards(Resource):
    # @cache.cached(timeout=360, query_string=True)
    def get(self):
        return get_all_udf_dashboards()


@address_profile_namespace.route("/v1/aci/udf_dashboards_data")
class UDFDashboards(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self):
        return get_all_udf_dashboards_data()


@address_profile_namespace.route("/v1/aci/daily_active_address")
class DailyAddress(Resource):
    @cache.cached(timeout=10, query_string=True)
    def get(self):
        time_range = flask.request.args.get("time_range", "7d")
        return get_daily_active_address(time_range)
