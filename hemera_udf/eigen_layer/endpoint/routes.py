from operator import and_
from typing import Optional, Union

from hemera.api.app.address.features import register_feature
from hemera.common.models import db
from hemera.common.models.tokens import Tokens
from hemera.common.utils.format_utils import bytes_to_hex_str, format_value_for_json, hex_str_to_bytes
from hemera_udf.eigen_layer.models.af_eigen_layer_address_current import AfEigenLayerAddressCurrent


@register_feature("eigen_layer", "value")
def get_eigen_layer_holdings(wallet_address: Optional[Union[str, bytes]]):
    if isinstance(wallet_address, str):
        address_bytes = hex_str_to_bytes(wallet_address)
    else:
        address_bytes = wallet_address

    query = db.session.query(AfEigenLayerAddressCurrent)
    query = query.filter(AfEigenLayerAddressCurrent.address == address_bytes, AfEigenLayerAddressCurrent.token != None)

    holdings = query.all()

    token_addresses = [(holding.token) for holding in holdings]

    tokens = Tokens.query.filter(
        and_(
            Tokens.address.in_(token_addresses),
            Tokens.is_verified == True,
        )
    ).all()

    token_map = {}
    res = []
    for token in tokens:
        token_map[token.address] = token
    tvl = 0
    for holder in holdings:
        if holder.token in token_map:
            token = token_map[holder.token]
            balance = (holder.deposit_amount or 0) - (holder.finish_withdraw_amount or 0)

            if balance > 0:
                # Convert Decimal to float for calculations
                decimals = int(token.decimals or 0)
                decimal_factor = 10**decimals

                # Convert all amounts to float before calculations
                balance_float = float(balance)
                price_float = float(token.price or 0)
                deposit_float = float(holder.deposit_amount or 0)
                finish_withdraw_float = float(holder.finish_withdraw_amount or 0)
                start_withdraw_float = float(holder.start_withdraw_amount or 0)

                res.append(
                    format_value_for_json(
                        {
                            "balance": balance_float / decimal_factor,
                            "strategy": holder.strategy,
                            "token": {
                                "address": bytes_to_hex_str(holder.token),
                                "token_name": token.name,
                                "token_symbol": token.symbol,
                                "token_logo_url": token.icon_url,
                                "token_type": token.token_type,
                                "extra_info": {
                                    "volume_24h": token.volume_24h,
                                    "price": price_float,
                                    "previous_price": token.previous_price,
                                    "market_cap": token.market_cap,
                                    "on_chain_market_cap": token.on_chain_market_cap,
                                    "cmc_id": token.cmc_id,
                                    "cmc_slug": token.cmc_slug,
                                    "gecko_id": token.gecko_id,
                                },
                            },
                            "tvl": (balance_float / decimal_factor) * price_float,
                            "deposit_amount": deposit_float / decimal_factor,
                            "finish_withdraw_amount": finish_withdraw_float / decimal_factor,
                            "start_withdraw_amount": start_withdraw_float / decimal_factor,
                        }
                    )
                )
                tvl += (balance_float / decimal_factor) * price_float
    return {
        "tvl": tvl,
        "total_value_usd": tvl,
        "holdings": res,
    }
