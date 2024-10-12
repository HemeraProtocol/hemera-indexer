import time
from typing import Any, Dict, Optional, Union

import flask
from flask import request
from flask_restx import Resource
from sqlalchemy import func

from api.app.address import address_features_namespace
from api.app.address.features import feature_registry, register_feature
from api.app.address.models import AddressBaseProfile, ScheduledMetadata
from api.app.cache import cache
from api.app.main import app
from common.models import db
from common.utils.exception_control import APIError
from common.utils.format_utils import as_dict, format_to_dict, hex_str_to_bytes
from indexer.modules.custom.address_index.endpoint.routes import (
    get_address_contract_operations,
    get_address_deploy_contract_count,
    get_address_first_deploy_contract_time,
)
from indexer.modules.custom.deposit_to_l2.endpoint.routes import ACIDepositToL2Current, ACIDepositToL2Transactions
from indexer.modules.custom.hemera_ens.endpoint.routes import ACIEnsCurrent, ACIEnsDetail
from indexer.modules.custom.opensea.endpoint.routes import ACIOpenseaProfile, ACIOpenseaTransactions
from indexer.modules.custom.uniswap_v3.endpoints.routes import (
    UniswapV3WalletLiquidityHolding,
    UniswapV3WalletTradingRecords,
    UniswapV3WalletTradingSummary,
)

PAGE_SIZE = 10
MAX_TRANSACTION = 500000
MAX_TRANSACTION_WITH_CONDITION = 10000
MAX_INTERNAL_TRANSACTION = 10000
MAX_TOKEN_TRANSFER = 10000

logger = app.logger


def get_address_recent_info(address: bytes, last_timestamp: int) -> dict:
    pass


def get_address_stats(address: Union[str, bytes]) -> dict:
    pass


def get_address_profile(address: Union[str, bytes]) -> dict:
    """
    Fetch and combine address profile data from both the base profile and recent transactions.
    """
    address_bytes = hex_str_to_bytes(address) if isinstance(address, str) else address

    # Fetch the base profile
    base_profile = db.session.query(AddressBaseProfile).filter_by(address=address_bytes).first()
    if not base_profile:
        raise APIError("No profile found for this address", code=400)

    # Convert base profile to a dictionary
    base_profile_data = as_dict(base_profile)

    # Fetch the latest scheduled metadata timestamp
    last_timestamp = db.session.query(func.max(ScheduledMetadata.last_data_timestamp)).scalar()
    """
    # Fetch recent transaction data from AddressOpenseaTransactions
    recent_data = get_address_recent_info(address_bytes, last_timestamp)

    # Merge recent transaction data with base profile data
    for key, value in recent_data.items():
        if key != "address":
            base_profile_data[key] += value

    # Fetch the latest transaction
    latest_transaction = get_latest_transaction_by_address(address_bytes)
    """
    # Combine and return the base profile, recent data, and latest transaction
    return base_profile_data


@address_features_namespace.route("/v1/aci/<address>/profile")
class ACIProfiles(Resource):
    @cache.cached(timeout=60)
    def get(self, address):
        address = address.lower()

        profile = get_address_profile(address)

        return profile, 200


@register_feature("contract_deployer", "value")
def get_contract_deployer_profile(address) -> Optional[Dict[str, Any]]:
    address_deploy_contract_count = get_address_deploy_contract_count(address)
    address_first_deploy_contract_time = get_address_first_deploy_contract_time(address)
    return (
        {
            "deployed_countract_count": address_deploy_contract_count,
            "first_deployed_time": address_first_deploy_contract_time,
        }
        if address_deploy_contract_count != 0
        else None
    )


@register_feature("contract_deployer", "events")
def get_contract_deployed_events(address, limit=5, offset=0) -> Optional[Dict[str, Any]]:
    count = get_address_deploy_contract_count(address)
    if count == 0:
        return None
    events = get_address_contract_operations(address, limit=limit, offset=offset)
    res = []
    for event in events:
        res.append(format_to_dict(event))
    return {"data": res, "total": count}


@address_features_namespace.route("/v1/aci/<address>/contract_deployer/profile")
class ACIContractDeployerProfile(Resource):
    def get(self, address):
        address = address.lower()
        return get_contract_deployer_profile(address) or {"deployed_countract_count": 0, "first_deployed_time": None}


@address_features_namespace.route("/v1/aci/<address>/contract_deployer/events")
class ACIContractDeployerEvents(Resource):
    def get(self, address):
        address = address.lower()
        page_index = int(flask.request.args.get("page", 1))
        page_size = int(flask.request.args.get("size", PAGE_SIZE))
        limit = page_size
        offset = (page_index - 1) * page_size

        return (get_contract_deployed_events(address, limit=limit, offset=offset) or {"data": [], "total": 0}) | {
            "size": page_size,
            "page": page_index,
        }


@address_features_namespace.route("/v1/aci/<address>/all_features")
class ACIAllFeatures(Resource):
    @cache.cached(timeout=3600, query_string=True)
    def get(self, address):
        address = address.lower()
        feature_list = [
            "ens",
            "opensea",
            "uniswap_v3_trading",
            "uniswap_v3_liquidity",
            "deposit_to_l2",
            "contract_deployer",
        ]
        features = flask.request.args.get("features")
        if features:
            feature_list = features.split(",")

        timer = time.time()
        feature_result = {}

        if "contract_deployer" in feature_list:
            # profile = get_address_profile(address)
            feature_result["contract_deployer"] = {
                "value": ACIContractDeployerProfile.get(self, address),
                "events": ACIContractDeployerEvents.get(self, address),
            }

        if "ens" in feature_list:
            feature_result["ens"] = {
                "value": ACIEnsCurrent.get(self, address),
                "events": ACIEnsDetail.get(self, address),
            }

        if "opensea" in feature_list:
            feature_result["opensea"] = {
                "value": ACIOpenseaProfile.get(self, address),
                "events": ACIOpenseaTransactions.get(self, address),
            }

        if "uniswap_v3_liquidity" in feature_list:
            holdings = UniswapV3WalletLiquidityHolding.get(self, address)
            feature_result["uniswap_v3_liquidity"] = {
                "value": {"pool_count": holdings["pool_count"], "total_value_usd": holdings["total_value_usd"]},
                "events": {"data": holdings["data"], "total": holdings["total"]},
            }

        if "uniswap_v3_trading" in feature_list:
            feature_result["uniswap_v3_trading"] = {
                "value": UniswapV3WalletTradingSummary.get(self, address),
                "events": UniswapV3WalletTradingRecords.get(self, address),
            }

        if "deposit_to_l2" in feature_list:
            feature_result["deposit_to_l2"] = {
                "value": ACIDepositToL2Current.get(self, address),
                "events": ACIDepositToL2Transactions.get(self, address),
            }

        feature_data_list = []
        for feature_id in feature_list:
            if feature_result.get(feature_id):
                feature_data_list.append(
                    {
                        "id": feature_id,
                        "value": feature_result.get(feature_id).get("value"),
                        "events": feature_result.get(feature_id).get("events"),
                    }
                )

        print(time.time() - timer)

        combined_result = {
            "address": address,
            "features": feature_data_list,
        }

        return combined_result, 200


@address_features_namespace.route("/v2/aci/<address>/all_features")
class ACIAllFeatures(Resource):
    def get(self, address):
        address = address.lower()
        requested_features = request.args.get("features")

        if requested_features:
            feature_list = [f for f in requested_features.split(",") if f in feature_registry.feature_list]
        else:
            feature_list = feature_registry.feature_list

        feature_result = {}
        total_start_time = time.time()

        for feature in feature_list:
            feature_start_time = time.time()
            feature_result[feature] = {}
            for subcategory in feature_registry.features[feature]:
                subcategory_start_time = time.time()
                try:
                    feature_result[feature][subcategory] = feature_registry.features[feature][subcategory](address)
                    subcategory_end_time = time.time()
                    logger.debug(
                        f"Feature '{feature}' subcategory '{subcategory}' execution time: {subcategory_end_time - subcategory_start_time:.4f} seconds"
                    )
                except Exception as e:
                    logger.error(f"Error in feature '{feature}' subcategory '{subcategory}': {str(e)}")
                    feature_result[feature][subcategory] = {"error": str(e)}

            feature_end_time = time.time()
            logger.debug(
                f"Total execution time for feature '{feature}': {feature_end_time - feature_start_time:.4f} seconds"
            )

        feature_data_list = [
            {"id": feature_id, **subcategory_dict}
            for feature_id in feature_list
            if (
                subcategory_dict := {
                    subcategory: feature_result[feature_id][subcategory]
                    for subcategory in feature_registry.features[feature_id]
                    if feature_result[feature_id][subcategory] is not None
                }
            )
        ]
        combined_result = {
            "address": address,
            "features": feature_data_list,
        }

        total_end_time = time.time()
        logger.debug(f"Total execution time for all features: {total_end_time - total_start_time:.4f} seconds")

        return combined_result, 200
