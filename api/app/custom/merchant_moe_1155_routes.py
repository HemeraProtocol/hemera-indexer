import binascii
import math
import re
from datetime import timedelta
from decimal import Decimal, getcontext
from operator import or_

from flask import request
from flask_restx import Resource
from sqlalchemy import and_, func

from api.app import explorer
from api.app.cache import cache
from api.app.custom import custom_namespace
from api.app.explorer import explorer_namespace
from common.models import db
from common.models import db as postgres_db
from common.models.tokens import Tokens
from common.utils.exception_control import APIError
from common.utils.format_utils import as_dict, format_to_dict, format_value_for_json, row_to_dict
from indexer.modules.custom.merchant_moe.models.feature_erc1155_token_current_holdings import (
    FeatureErc1155TokenCurrentHoldings,
)
from indexer.modules.custom.merchant_moe.models.feature_merchant_moe_pool import FeatureMerChantMoePools
from indexer.modules.custom.merchant_moe.models.feature_erc1155_token_current_supply import (
    FeatureErc1155TokenCurrentSupplyStatus,
)
from indexer.modules.custom.merchant_moe.models.feature_merchant_moe_token_current_bin import (
    FeatureMerChantMoeTokenBinCurrentStatus,
)


@custom_namespace.route("/v1/merchant_moe_1155/<wallet_address>")
class MerchantMoe1155(Resource):
    def get(self, wallet_address):
        pool_infos = {}
        pool_tokens = (
            db.session.query(FeatureMerChantMoePools)
            .all()
        )

        tokens = set()
        for data in pool_tokens:
            tokens.add(data.token0_address)
            tokens.add(data.token1_address)
            pool_infos["0x" + data.token_address.hex()] = {
                "getTokenX": "0x" + data.token0_address.hex(),
                "getTokenY": "0x" + data.token1_address.hex()
            }
        wallet_address = wallet_address.lower()
        address_bytes = bytes.fromhex(wallet_address[2:])
        holdings = (
            db.session.query(FeatureErc1155TokenCurrentHoldings)
            .filter(
                FeatureErc1155TokenCurrentHoldings.wallet_address == address_bytes,
                FeatureErc1155TokenCurrentHoldings.balance > 0,
            )
            .all()
        )
        # get totalSupply
        unique_token_addresses = {holding.token_address for holding in holdings}

        total_supply_list = (
            db.session.query(FeatureErc1155TokenCurrentSupplyStatus)
            .filter(FeatureErc1155TokenCurrentSupplyStatus.token_address.in_(unique_token_addresses))
            .all()
        )

        token_bin_list = (
            db.session.query(FeatureMerChantMoeTokenBinCurrentStatus)
            .filter(FeatureMerChantMoeTokenBinCurrentStatus.token_address.in_(unique_token_addresses))
            .all()
        )

        total_supply_map = {}
        token_bin_map = {}
        for data in total_supply_list:
            key = (data.token_address, data.token_id)
            total_supply_map[key] = data.total_supply
        for data in token_bin_list:
            key = (data.token_address, data.token_id)
            token_bin_map[key] = data
        token_id_infos = {}

        erc20_datas = db.session.query(Tokens).filter(Tokens.address.in_(tokens)).all()
        erc20_infos = {}
        for data in erc20_datas:
            erc20_infos["0x" + data.address.hex()] = data

        result = []
        token_total_amount = {}
        for holding in holdings:
            nft_address = "0x" + holding.token_address.hex()
            token_info = pool_infos[nft_address]
            token0_address = token_info["getTokenX"]
            token1_address = token_info["getTokenY"]
            token_id = holding.token_id
            key = (holding.token_address, token_id)
            total_supply = total_supply_map[key]
            token_bin = token_bin_map[key]
            token_bin0 = token_bin.reserve0_bin
            token_bin1 = token_bin.reserve1_bin
            rate = holding.balance / total_supply
            token0_balance = token_bin0 * rate
            token1_balance = token_bin1 * rate
            token0_info = erc20_infos[token0_address]
            token1_info = erc20_infos[token1_address]

            amount0_human = token0_balance / 10 ** token0_info.decimals
            amount1_human = token1_balance / 10 ** token1_info.decimals
            if token0_address not in token_total_amount:
                token_total_amount[token0_address] = amount0_human
            else:
                token_total_amount[token0_address] = amount0_human + token_total_amount[token0_address]
            if token1_address not in token_total_amount:
                token_total_amount[token1_address] = amount1_human
            else:
                token_total_amount[token1_address] = amount1_human + token_total_amount[token1_address]
            result.append(
                {
                    "nft_address": nft_address,
                    "token_id": str(token_id),
                    "token0": {
                        "token0_symbol": token0_info.symbol,
                        "token0_balance": str(amount0_human),
                    },
                    "token1": {
                        "token1_symbol": token1_info.symbol,
                        "token1_balance": str(amount1_human),
                    },
                }
            )
        for key, value in token_total_amount.items():
            token_total_amount[key] = str(value)

        return {"detail": result, "token_all": token_total_amount}, 200
