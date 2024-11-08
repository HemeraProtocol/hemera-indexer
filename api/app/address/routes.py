import time

from flask import request
from flask_restx import Resource

from api.app.address import address_features_namespace
from api.app.address.features import feature_registry
from api.app.main import app

PAGE_SIZE = 10
MAX_TRANSACTION = 500000
MAX_TRANSACTION_WITH_CONDITION = 10000
MAX_INTERNAL_TRANSACTION = 10000
MAX_TOKEN_TRANSFER = 10000

logger = app.logger


@address_features_namespace.route("/v1/aci/<address>/all_features")
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
