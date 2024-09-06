import binascii
import math
import re
from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from operator import or_

from flask import request
from flask_restx import Resource
from sqlalchemy import and_, func

from api.app import explorer
from api.app.cache import cache
from api.app.explorer import explorer_namespace
from common.models import db
from common.models import db as postgres_db
from common.models.tokens import Tokens
from common.utils.exception_control import APIError
from common.utils.format_utils import as_dict, format_to_dict, format_value_for_json, row_to_dict
from common.utils.web3_utils import is_eth_address
from indexer.modules.custom.uniswap_v3.endpoints import uniswap_v3_namespace
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_liquidity_records import UniswapV3TokenLiquidityRecords
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pool_current_prices import UniswapV3PoolCurrentPrices
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_token_current_status import UniswapV3TokenCurrentStatus
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_tokens import UniswapV3Tokens

Q96 = 2**96


@uniswap_v3_namespace.route("/v1/aci/<wallet_address>/uniswapv3/current_holding")
class UniswapV3WalletHolding(Resource):
    def get(self, wallet_address):
        wallet_address = wallet_address.lower()
        address_bytes = bytes.fromhex(wallet_address[2:])
        holdings = (
            db.session.query(UniswapV3TokenCurrentStatus)
            .filter(UniswapV3TokenCurrentStatus.wallet_address == address_bytes)
            .all()
        )

        unique_pool_addresses = {holding.pool_address for holding in holdings}
        pool_prices = (
            db.session.query(UniswapV3PoolCurrentPrices)
            .filter(UniswapV3PoolCurrentPrices.pool_address.in_(unique_pool_addresses))
            .all()
        )
        pool_price_map = {}
        for data in pool_prices:
            pool_address = "0x" + data.pool_address.hex()
            pool_price_map[pool_address] = data.sqrt_price_x96

        tokenIds = db.session.query(UniswapV3Tokens).all()
        token_id_infos = {}
        erc20_tokens = set()
        pool_infos = {}
        pools = db.session.query(UniswapV3Pools).filter(UniswapV3Pools.pool_address.in_(unique_pool_addresses)).all()
        for data in pools:
            pool_address = "0x" + data.pool_address.hex()
            pool_infos[pool_address] = data
            erc20_tokens.add(data.token0_address)
            erc20_tokens.add(data.token1_address)

        erc20_datas = db.session.query(Tokens).filter(Tokens.address.in_(erc20_tokens)).all()
        erc20_infos = {}
        for data in erc20_datas:
            erc20_infos["0x" + data.address.hex()] = data

        for token in tokenIds:
            nft_address = "0x" + token.nft_address.hex()
            token_id = token.token_id
            key = (nft_address, token_id)
            token_id_infos[key] = token

        result = []
        for holding in holdings:
            nft_address = "0x" + holding.nft_address.hex()
            token_id = holding.token_id
            pool_address = "0x" + holding.pool_address.hex()
            sqrt_price = pool_price_map[pool_address]
            token_id_info = token_id_infos[(nft_address, token_id)]
            pool_info = pool_infos[pool_address]
            token0_address = "0x" + pool_info.token0_address.hex()
            token1_address = "0x" + pool_info.token1_address.hex()
            if token0_address in erc20_infos:
                token0_info = erc20_infos[token0_address]
            else:
                token0_info = Tokens(symbol="None", decimals=18)
            if token1_address in erc20_infos:
                token1_info = erc20_infos[token1_address]
            else:
                token1_info = Tokens(symbol="None", decimals=18)
            amount0_str, amount1_str = get_token_amounts(
                holding.liquidity,
                sqrt_price,
                token_id_info.tick_lower,
                token_id_info.tick_upper,
                token0_info.decimals,
                token1_info.decimals,
            )
            result.append(
                {
                    "nft_address": nft_address,
                    "token_id": str(token_id),
                    "token0": {
                        "token0_symbol": token0_info.symbol,
                        "token0_balance": amount0_str,
                    },
                    "token1": {
                        "token1_symbol": token1_info.symbol,
                        "token1_balance": amount1_str,
                    },
                }
            )

        return result, 200


@uniswap_v3_namespace.route("/v1/aci/<wallet_address>/uniswapv3/first_liquidity_time")
class UniswapV3WalletLiquidityDetail(Resource):
    def get(self, wallet_address):
        wallet_address = wallet_address.lower()
        address_bytes = bytes.fromhex(wallet_address[2:])
        first_holding = (
            db.session.query(UniswapV3TokenLiquidityRecords)
            .filter(UniswapV3TokenLiquidityRecords.owner == address_bytes)
            .first()
        )
        if not first_holding:
            return {
                "message": "no provide history",
            }, 200
        dt_object = datetime.utcfromtimestamp(first_holding.block_timestamp)
        first_provide_time = dt_object.strftime("%Y-%m-%d %H:%M:%S")
        return {
            "first_provide_time": first_provide_time,
            "token_id": str(first_holding.token_id),
            "token0_address": first_holding.token0_address,
            "token1_address": first_holding.token1_address,
        }, 200


@uniswap_v3_namespace.route("/v1/aci/<wallet_address>/uniswapv3/provide_liquidity_pool_count")
class UniswapV3WalletLiquidityDetail(Resource):
    def get(self, wallet_address):
        wallet_address = wallet_address.lower()
        address_bytes = bytes.fromhex(wallet_address[2:])
        count = (
            db.session.query(UniswapV3TokenLiquidityRecords.pool_address)
            .filter(UniswapV3TokenLiquidityRecords.owner == address_bytes)
            .distinct()
            .count()
        )
        return {"provide_pool_count": count}, 200


def get_tick_at_sqrt_ratio(sqrt_price_x96):
    tick = math.floor(math.log((sqrt_price_x96 / Q96) ** 2) / math.log(1.0001))
    return tick


def get_token_amounts(liquidity, sqrt_price_x96, tick_low, tick_high, token0_decimal, token1_decimal):
    liquidity = float(liquidity)
    sqrt_price_x96 = float(sqrt_price_x96)
    tick_low = float(tick_low)
    tick_high = float(tick_high)
    sqrt_ratio_a = math.sqrt(1.0001**tick_low)
    sqrt_ratio_b = math.sqrt(1.0001**tick_high)

    current_tick = get_tick_at_sqrt_ratio(sqrt_price_x96)
    sqrt_price = sqrt_price_x96 / Q96

    amount0_wei = 0
    amount1_wei = 0

    if current_tick <= tick_low:
        amount0_wei = math.floor(liquidity * ((sqrt_ratio_b - sqrt_ratio_a) / (sqrt_ratio_a * sqrt_ratio_b)))
    elif current_tick > tick_high:
        amount1_wei = math.floor(liquidity * (sqrt_ratio_b - sqrt_ratio_a))
    elif tick_low <= current_tick < tick_high:
        amount0_wei = math.floor(liquidity * ((sqrt_ratio_b - sqrt_price) / (sqrt_price * sqrt_ratio_b)))
        amount1_wei = math.floor(liquidity * (sqrt_price - sqrt_ratio_a))

    amount0_human = amount0_wei / 10**token0_decimal
    amount1_human = amount1_wei / 10**token1_decimal
    amount0_str = f"{amount0_human:.{token0_decimal}f}"
    amount1_str = f"{amount1_human:.{token1_decimal}f}"
    return [amount0_str, amount1_str]
