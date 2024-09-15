from time import time
from typing import Union

import flask
from flask_restx import Resource
from sqlalchemy import func

from api.app.address import address_features_namespace
from api.app.address.models import AddressBaseProfile, ScheduledMetadata
from api.app.af_ens.routes import ACIEnsCurrent, ACIEnsDetail
from api.app.cache import cache
from api.app.deposit_to_l2.routes import ACIDepositToL2Current, ACIDepositToL2Transactions
from common.models import db
from common.utils.exception_control import APIError
from common.utils.format_utils import as_dict, format_to_dict
from indexer.modules.custom.address_index.endpoint.routes import (
    get_address_contract_operations,
    get_address_deploy_contract_count,
    get_address_first_deploy_contract_time,
)
from indexer.modules.custom.opensea.endpoint.routes import ACIOpenseaProfile, ACIOpenseaTransactions
from indexer.modules.custom.uniswap_v3.endpoints.routes import (
    UniswapV3WalletLiquidityDetail,
    UniswapV3WalletLiquidityHolding,
    UniswapV3WalletTradingRecords,
    UniswapV3WalletTradingSummary,
)

PAGE_SIZE = 10
MAX_TRANSACTION = 500000
MAX_TRANSACTION_WITH_CONDITION = 10000
MAX_INTERNAL_TRANSACTION = 10000
MAX_TOKEN_TRANSFER = 10000


def get_address_recent_info(address: bytes, last_timestamp: int) -> dict:
    pass


def get_address_stats(address: Union[str, bytes]) -> dict:
    pass


def get_address_profile(address: Union[str, bytes]) -> dict:
    """
    Fetch and combine address profile data from both the base profile and recent transactions.
    """
    address_bytes = bytes.fromhex(address[2:]) if isinstance(address, str) else address

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


@address_features_namespace.route("/v1/aci/<address>/contract_deployer/profile")
class ACIContractDeployerProfile(Resource):
    def get(self, address):
        address = address.lower()
        return {
            "deployed_countract_count": get_address_deploy_contract_count(address),
            "first_deployed_time": get_address_first_deploy_contract_time(address),
        }


@address_features_namespace.route("/v1/aci/<address>/contract_deployer/events")
class ACIContractDeployerEvents(Resource):
    def get(self, address):
        address = address.lower()
        events = get_address_contract_operations(address)
        res = []
        for event in events:
            res.append(format_to_dict(event))
        return {"data": res}


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

        timer = time()
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

        print(time() - timer)

        combined_result = {
            "address": address,
            "features": feature_data_list,
        }

        return combined_result, 200
