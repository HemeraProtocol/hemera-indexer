from typing import Union

from flask_restx import Resource
from sqlalchemy import func

from api.app.address import address_features_namespace
from api.app.address.models import AddressBaseProfile, ScheduledMetadata
from api.app.af_ens.routes import ACIEnsCurrent, ACIEnsDetail
from api.app.cache import cache
from api.app.deposit_to_l2.routes import ExplorerDepositBridgeTimes, ExplorerDepositCurrent
from common.models import db
from common.utils.exception_control import APIError
from common.utils.format_utils import as_dict
from indexer.modules.custom.opensea.endpoint.routes import ACIOpenseaProfile, ACIOpenseaTransactions
from indexer.modules.custom.uniswap_v3.endpoints.routes import UniswapV3WalletHolding, UniswapV3WalletLiquidityDetail

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


@address_features_namespace.route("/v1/aci/<address>/all_features")
class ACIAllFeatures(Resource):
    @cache.cached(timeout=60)
    def get(self, address):
        address = address.lower()

        ens_data = {"ens_current": ACIEnsCurrent.get(self, address), "ens_detail": ACIEnsDetail.get(self, address)}

        opensea_data = {
            "opensea_profile": ACIOpenseaProfile.get(self, address),
            "opensea_transactions": ACIOpenseaTransactions.get(self, address),
        }

        uniswap_data = {
            "uniswap_v3_holding": UniswapV3WalletHolding.get(self, address),
            "uniswap_v3_detail": UniswapV3WalletLiquidityDetail.get(self, address),
        }

        deposited_data = {
            "deposited_current": ExplorerDepositCurrent.get(self, address),
            "deposited_bridge_times": ExplorerDepositBridgeTimes.get(self, address),
        }

        combined_result = {
            "address": address,
            "ens_data": ens_data,
            "opensea_data": opensea_data,
            "uniswap_data": uniswap_data,
            "deposited_data": deposited_data,
        }

        return combined_result, 200
