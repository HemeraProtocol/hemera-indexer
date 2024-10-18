from functools import wraps

from flask import jsonify
from flask_restx import fields

from api.app.address import address_features_namespace


def validate_eth_address(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        address = kwargs.get("address")
        if not address:
            return jsonify({"code": 400, "message": "Address is required", "data": None}), 400

        try:
            # Remove '0x' prefix if present and convert to lowercase
            address = address.lower()
            if address.startswith("0x"):
                address = address[2:]

            # Validate address format (assuming Ethereum-like addresses)
            if len(address) != 40 or not all(c in "0123456789abcdef" for c in address):
                raise ValueError("Invalid address format")

            # Add '0x' prefix back
            address = "0x" + address

            # Replace the address in kwargs
            kwargs["address"] = address

            # Call the original function
            return f(*args, **kwargs)
        except ValueError as e:
            return {"code": 400, "message": str(e), "data": None}, 400

    return decorated_function


def filter_and_fill_dict_by_model(data: dict, model: dict) -> dict:
    """
    Filter a dictionary to only include keys that are defined in the Flask-RESTX model
    and fill in default values for missing or None fields.

    This function recursively processes nested models and handles various field types.

    :param data: The dictionary to filter and fill
    :param model: The Flask-RESTX model to use for filtering and filling
    :return: A new dictionary with only the keys defined in the model, including default values
    """
    result = {}
    for key, field in model.items():
        if key in data and data[key] is not None:
            if isinstance(field, fields.Nested):
                if isinstance(data[key], dict):
                    result[key] = filter_and_fill_dict_by_model(data[key], field.model)
                elif isinstance(data[key], list) and field.as_list:
                    result[key] = [
                        filter_and_fill_dict_by_model(item, field.model) for item in data[key] if isinstance(item, dict)
                    ]
                else:
                    result[key] = get_default_value(field)
            elif isinstance(field, fields.List) and isinstance(field.container, fields.Nested):
                if isinstance(data[key], list):
                    result[key] = [
                        filter_and_fill_dict_by_model(item, field.container.model)
                        for item in data[key]
                        if isinstance(item, dict)
                    ]
                else:
                    result[key] = []
            else:
                result[key] = data[key]
        else:
            result[key] = get_default_value(field)

    return result


def get_default_value(field):
    """
    Get the default value for a given Flask-RESTX field.

    :param field: Flask-RESTX field
    :return: Appropriate default value for the field type
    """
    if hasattr(field, "default") and field.default is not None:
        return field.default
    elif isinstance(field, fields.Integer):
        return 0
    elif isinstance(field, fields.Float):
        return 0.0
    elif isinstance(field, fields.Boolean):
        return False
    elif isinstance(field, fields.String):
        return ""
    elif isinstance(field, fields.DateTime):
        return None  # or you could return a default datetime
    elif isinstance(field, fields.List):
        return []
    elif isinstance(field, fields.Nested):
        return {}
    else:
        return None


def create_standard_response_model(name, data_model):
    """
    Factory function to create a standard response model.

    This function creates a consistent response structure with 'code', 'message', and 'data' fields,
    where 'data' is a nested field that can vary based on the provided data model.

    :param name: Name of the model, used to create a unique model name
    :param data_model: The data model to be nested in the 'data' field
    :return: A Flask-RESTX model representing the standard response structure
    """
    return address_features_namespace.model(
        f"StandardResponse{name}",
        {
            "code": fields.Integer(required=True, description="Response status code"),
            "message": fields.String(required=True, description="Response message"),
            "data": fields.Nested(data_model, description="Response data"),
        },
    )


token_extra_info_model = address_features_namespace.model(
    "TokenExtraInfo",
    {
        "volume_24h": fields.String(description="Volume in the last 24 hours"),
        "price": fields.String(description="Price"),
        "previous_price": fields.String(description="Previous price"),
        "market_cap": fields.String(description="Market cap"),
        "on_chain_market_cap": fields.String(description="On-chain market cap"),
        "cmc_id": fields.Integer(description="CoinMarketCap ID"),
        "cmc_slug": fields.String(description="CoinMarketCap slug"),
        "gecko_id": fields.String(description="CoinGecko ID"),
    },
)

token_info_model = address_features_namespace.model(
    "TokenInfo",
    {
        "address": fields.String(required=True, description="Token address"),
        "token_name": fields.String(description="Token name"),
        "token_symbol": fields.String(description="Token symbol"),
        "token_type": fields.String(description="Token type"),
        "token_logo_url": fields.String(description="Token logo URL"),
        "extra_info": fields.Nested(token_extra_info_model, description="Extra token information"),
    },
)

token_holding_model = address_features_namespace.model(
    "TokenHolding",
    {
        "token": fields.Nested(token_info_model, description="Token information"),
        "balance": fields.String(description="Token balance"),
        "tvl": fields.String(description="Token TVL"),
    },
)

address_base_info_model = address_features_namespace.model(
    "AddressBaseInfo",
    {
        "address": fields.String(required=True, description="User address"),
        "is_contract": fields.Boolean(description="Is contract"),
        "init_funding_from_address": fields.String(description="Initial funding from address"),
        "init_funding_value": fields.String(description="Initial funding value"),
        "init_funding_transaction_hash": fields.String(description="Initial funding transaction hash"),
        "init_funding_block_timestamp": fields.DateTime(description="Initial funding block timestamp"),
        "init_block_hash": fields.String(description="Initial block hash"),
        "init_block_number": fields.Integer(description="Initial block number"),
        "creation_code": fields.String(allow_null=True, description="Creation code"),
        "deployed_code": fields.String(allow_null=True, description="Deployed code"),
        "deployed_block_timestamp": fields.DateTime(allow_null=True, description="Deployed block timestamp"),
        "deployed_block_number": fields.Integer(allow_null=True, description="Deployed block number"),
        "deployed_block_hash": fields.String(allow_null=True, description="Deployed block hash"),
        "deployed_transaction_hash": fields.String(allow_null=True, description="Deployed transaction hash"),
        "deployed_internal_transaction_from_address": fields.String(
            allow_null=True, description="Deployed internal transaction from address"
        ),
        "deployed_transaction_from_address": fields.String(
            allow_null=True, description="Deployed transaction from address"
        ),
        "first_transaction_hash": fields.String(description="First transaction hash"),
        "first_block_hash": fields.String(description="First block hash"),
        "first_block_number": fields.Integer(description="First block number"),
        "first_block_timestamp": fields.DateTime(description="First block timestamp"),
        "first_to_address": fields.String(description="First to address"),
        "latest_transaction_hash": fields.String(description="Latest transaction hash"),
        "latest_block_hash": fields.String(description="Latest block hash"),
        "latest_block_number": fields.Integer(description="Latest block number"),
        "latest_block_timestamp": fields.DateTime(description="Latest block timestamp"),
        "latest_to_address": fields.String(description="Latest to address"),
        "transaction_count": fields.Integer(default=0, description="Transaction count"),
        "transaction_in_count": fields.Integer(default=0, description="Transaction in count"),
        "transaction_out_count": fields.Integer(default=0, description="Transaction out count"),
        "transaction_self_count": fields.Integer(default=0, description="Transaction self count"),
        "transaction_in_value": fields.String(default="0", description="Transaction in value"),
        "transaction_out_value": fields.String(default="0", description="Transaction out value"),
        "transaction_self_value": fields.String(default="0", description="Transaction self value"),
        "transaction_in_fee": fields.String(default="0", description="Transaction in fee"),
        "transaction_out_fee": fields.String(default="0", description="Transaction out fee"),
        "transaction_self_fee": fields.String(default="0", description="Transaction self fee"),
        "internal_transaction_count": fields.Integer(default=0, description="Internal transaction count"),
        "internal_transaction_in_count": fields.Integer(default=0, description="Internal transaction in count"),
        "internal_transaction_out_count": fields.Integer(default=0, description="Internal transaction out count"),
        "internal_transaction_self_count": fields.Integer(default=0, description="Internal transaction self count"),
        "internal_transaction_in_value": fields.String(default="0", description="Internal transaction in value"),
        "internal_transaction_out_value": fields.String(default="0", description="Internal transaction out value"),
        "internal_transaction_self_value": fields.String(default="0", description="Internal transaction self value"),
    },
)

daily_volume_model = address_features_namespace.model(
    "DailyVolume",
    {
        "date": fields.String(description="Date of the volume"),
        "volume_eth": fields.String(description="Daily volume in ETH"),
        "price": fields.String(description="ETH price on that day"),
        "volume_usd": fields.String(description="Daily volume in USD"),
    },
)

volume_summary_model = address_features_namespace.model(
    "VolumeSummary",
    {
        "total_volume_eth": fields.String(description="Total volume in ETH"),
        "total_volume_usd": fields.String(description="Total volume in USD"),
        "average_daily_volume_eth": fields.String(description="Average daily volume in ETH"),
        "average_daily_volume_usd": fields.String(description="Average daily volume in USD"),
    },
)

address_volumes_model = address_features_namespace.model(
    "AddressVolumes",
    {
        "daily_volumes": fields.List(fields.Nested(daily_volume_model), description="Daily volume data"),
        "summary": fields.Nested(volume_summary_model, description="Volume summary"),
    },
)

asset_model = address_features_namespace.model(
    "Asset",
    {
        "total_asset_value_usd": fields.String(description="Total asset value in USD"),
        "coin_balance": fields.String(description="Coin balance"),
        "holdings": fields.List(fields.Nested(token_holding_model), description="Token holdings"),
    },
)

aci_score_model = address_features_namespace.model(
    "ACIScore",
    {
        "score": fields.Float(description="ACI score"),
        "base_info": fields.Nested(address_base_info_model, description="Base information"),
        "assets": fields.Nested(asset_model, description="Assets"),
        "volumes": fields.Nested(address_volumes_model, description="Volumes"),
    },
)

address_base_info_response_model = create_standard_response_model("AddressProfile", address_base_info_model)

aci_score_response_model = create_standard_response_model("ACIScore", aci_score_model)
