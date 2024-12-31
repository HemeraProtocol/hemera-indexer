import math
from datetime import datetime
from typing import Any, Dict, Optional

from flask import request
from flask_restx import Resource
from sqlalchemy.sql import select, tuple_

from api.app.address.features import register_feature
from api.app.db_service.tokens import get_token_price_map_by_symbol_list
from common.models import db
from common.models.tokens import Tokens
from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from indexer.modules.custom.uniswap_v3.endpoints import uniswap_v3_namespace
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_liquidity_records import UniswapV3TokenLiquidityRecords
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pool_current_prices import UniswapV3PoolCurrentPrices
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_pools import UniswapV3Pools
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_swap_records import UniswapV3PoolSwapRecords
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_token_current_status import UniswapV3TokenCurrentStatus
from indexer.modules.custom.uniswap_v3.models.feature_uniswap_v3_tokens import UniswapV3Tokens

Q96 = 2**96
PAGE_SIZE = 10

STABLE_COINS = {
    "0xdac17f958d2ee523a2206206994597c13d831ec7": "USDT",
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "USDC",
    "0x6b175474e89094c44da98b954eedeac495271d0f": "DAI",
}

NATIVE_COINS = {
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "WETH",
}


@register_feature("uniswap_v3_trading", "value")
def get_uniswap_v3_trading_value(address) -> Optional[Dict[str, Any]]:
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    swaps = db.session.execute(
        select(
            UniswapV3PoolSwapRecords.transaction_hash,
            UniswapV3PoolSwapRecords.token0_address,
            UniswapV3PoolSwapRecords.token1_address,
            UniswapV3PoolSwapRecords.amount0,
            UniswapV3PoolSwapRecords.amount1,
        )
        .where(UniswapV3PoolSwapRecords.transaction_from_address == address)
        .order_by(UniswapV3PoolSwapRecords.block_timestamp.desc())
    ).all()

    token_list = []
    transaction_hash_list = []

    for swap in swaps:
        token_list.append(swap.token0_address)
        token_list.append(swap.token1_address)
        transaction_hash_list.append(swap.transaction_hash)

    token_list = list(set(token_list))
    transaction_hash_list = list(set(transaction_hash_list))
    if len(transaction_hash_list) == 0 or len(token_list) == 0:
        return None
    return {
        "trade_count": len(transaction_hash_list),
        "trade_asset_count": len(token_list),
        "total_volume_usd": 0,
        "average_value_usd": 0,
    }


@register_feature("uniswap_v3_trading", "events")
def get_uniswap_v3_trading_events(address, limit=5, offset=0) -> Optional[Dict[str, Any]]:
    if isinstance(address, str):
        address = hex_str_to_bytes(address)
    total_count = UniswapV3PoolSwapRecords.query.where(
        UniswapV3PoolSwapRecords.transaction_from_address == address
    ).count()
    if total_count == 0:
        return None

    swaps = (
        db.session.execute(
            select(UniswapV3PoolSwapRecords)
            .where(UniswapV3PoolSwapRecords.transaction_from_address == address)
            .order_by(UniswapV3PoolSwapRecords.block_timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )
    swap_records = []
    token_list = []
    for swap in swaps:
        token_list.append(swap.token0_address)
        token_list.append(swap.token1_address)

    tokens = db.session.execute(select(Tokens).where(Tokens.address.in_(list(set(token_list))))).scalars().all()

    token_map = {token.address: token for token in tokens}

    for swap in swaps:
        token0 = token_map.get(swap.token0_address)
        token1 = token_map.get(swap.token1_address)
        swap_records.append(
            {
                "block_number": swap.block_number,
                "block_timestamp": datetime.fromtimestamp(swap.block_timestamp).isoformat("T", "seconds"),
                "transaction_hash": bytes_to_hex_str(swap.transaction_hash),
                "pool_address": bytes_to_hex_str(swap.pool_address),
                "amount0": "{0:.18f}".format(abs(swap.amount0) / 10**token0.decimals).rstrip("0").rstrip("."),
                "amount1": "{0:.18f}".format(abs(swap.amount1) / 10**token1.decimals).rstrip("0").rstrip("."),
                "token0_address": bytes_to_hex_str(swap.token0_address),
                "token0_symbol": token0.symbol,
                "token0_name": token0.name,
                "token0_icon_url": token0.icon_url,
                "token1_address": bytes_to_hex_str(swap.token1_address),
                "token1_symbol": token1.symbol,
                "token1_name": token1.name,
                "token1_icon_url": token1.icon_url,
                "action_type": get_swap_action_type(swap),
            }
        )

    return {
        "data": swap_records,
        "total": total_count,
    }


@uniswap_v3_namespace.route("/v1/aci/<address>/uniswap_v3_trading/swaps")
class UniswapV3WalletTradingRecords(Resource):
    def get(self, address):
        address = address.lower()
        page_index = int(request.args.get("page", 1))
        page_size = int(request.args.get("size", PAGE_SIZE))

        return (
            get_uniswap_v3_trading_events(address, page_size, (page_index - 1) * page_size) or {"data": [], "total": 0}
        ) | {
            "page": page_index,
            "size": page_size,
        }


@uniswap_v3_namespace.route("/v1/aci/<address>/uniswap_v3_trading/summary")
class UniswapV3WalletTradingSummary(Resource):
    def get(self, address):
        address = address.lower()
        return get_uniswap_v3_trading_value(address) or {
            "trade_count": 0,
            "trade_asset_count": 0,
            "total_volume_usd": 0,
            "average_value_usd": 0,
        }


@register_feature("uniswap_v3_liquidity", "value")
def get_uniswap_v3_liquidity_value(address) -> Optional[Dict[str, Any]]:
    address = address.lower()
    address_bytes = hex_str_to_bytes(address)

    # Get all LP holdings
    holdings = (
        db.session.query(UniswapV3TokenCurrentStatus)
        .filter(UniswapV3TokenCurrentStatus.wallet_address == address_bytes)
        .filter(UniswapV3TokenCurrentStatus.liquidity > 0)
        .all()
    )

    # Get Pool Price
    unique_pool_addresses = {holding.pool_address for holding in holdings}
    pool_prices = (
        db.session.query(UniswapV3PoolCurrentPrices)
        .filter(UniswapV3PoolCurrentPrices.pool_address.in_(unique_pool_addresses))
        .all()
    )
    pool_price_map = {}
    for data in pool_prices:
        pool_address = bytes_to_hex_str(data.pool_address)
        pool_price_map[pool_address] = data.sqrt_price_x96

    # Get token id info
    token_id_list = [(holding.position_token_address, holding.token_id) for holding in holdings]
    tokenIds = (
        db.session.query(UniswapV3Tokens)
        .filter(tuple_(UniswapV3Tokens.position_token_address, UniswapV3Tokens.token_id).in_(token_id_list))
        .all()
    )
    token_id_infos = {}
    for token in tokenIds:
        position_token_address = bytes_to_hex_str(token.position_token_address)
        token_id = token.token_id
        key = (position_token_address, token_id)
        token_id_infos[key] = token

    # Get Token info
    erc20_tokens = set()
    pool_infos = {}
    pools = db.session.query(UniswapV3Pools).filter(UniswapV3Pools.pool_address.in_(unique_pool_addresses)).all()
    for data in pools:
        pool_address = bytes_to_hex_str(data.pool_address)
        pool_infos[pool_address] = data
        erc20_tokens.add(data.token0_address)
        erc20_tokens.add(data.token1_address)

    erc20_datas = db.session.query(Tokens).filter(Tokens.address.in_(erc20_tokens)).all()
    erc20_infos = {}
    token_symbol_list = []
    for data in erc20_datas:
        erc20_infos[bytes_to_hex_str(data.address)] = data
        token_symbol_list.append(data.symbol)

    # Get Token Price
    token_price_map = get_token_price_map_by_symbol_list(list(set(token_symbol_list)))

    result = []
    total_value_usd = 0
    for holding in holdings:
        position_token_address = bytes_to_hex_str(holding.position_token_address)
        token_id = holding.token_id
        pool_address = bytes_to_hex_str(holding.pool_address)
        sqrt_price = pool_price_map[pool_address]
        token_id_info = token_id_infos[(position_token_address, token_id)]
        pool_info = pool_infos[pool_address]
        token0_address = bytes_to_hex_str(pool_info.token0_address)
        token1_address = bytes_to_hex_str(pool_info.token1_address)
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
        token0_value_usd = float(amount0_str) * float(token_price_map.get(token0_info.symbol, 0))
        token1_value_usd = float(amount1_str) * float(token_price_map.get(token1_info.symbol, 0))
        total_value_usd += token0_value_usd
        total_value_usd += token1_value_usd
        result.append(
            {
                "pool_address": pool_address,
                "position_token_address": position_token_address,
                "token_id": str(token_id),
                "block_timestamp": holding.block_timestamp.isoformat("T", "seconds"),
                "token0": {
                    "token0_symbol": token0_info.symbol,
                    "token0_icon_url": token0_info.icon_url,
                    "token0_balance": amount0_str,
                    "token0_value_usd": token0_value_usd,
                },
                "token1": {
                    "token1_symbol": token1_info.symbol,
                    "token1_icon_url": token1_info.icon_url,
                    "token1_balance": amount1_str,
                    "token1_value_usd": token1_value_usd,
                },
            }
        )
    if len(result) == 0:
        return None

    return {
        "pool_count": len(unique_pool_addresses),
        "total_value_usd": total_value_usd,
    }


@register_feature("uniswap_v3_liquidity", "events")
def get_uniswap_v3_liquidity_events(address) -> Optional[Dict[str, Any]]:
    address = address.lower()
    address_bytes = hex_str_to_bytes(address)

    # Get all LP holdings
    holdings = (
        db.session.query(UniswapV3TokenCurrentStatus)
        .filter(UniswapV3TokenCurrentStatus.wallet_address == address_bytes)
        .filter(UniswapV3TokenCurrentStatus.liquidity > 0)
        .all()
    )

    # Get Pool Price
    unique_pool_addresses = {holding.pool_address for holding in holdings}
    pool_prices = (
        db.session.query(UniswapV3PoolCurrentPrices)
        .filter(UniswapV3PoolCurrentPrices.pool_address.in_(unique_pool_addresses))
        .all()
    )
    pool_price_map = {}
    for data in pool_prices:
        pool_address = bytes_to_hex_str(data.pool_address)
        pool_price_map[pool_address] = data.sqrt_price_x96

    # Get token id info
    token_id_list = [(holding.position_token_address, holding.token_id) for holding in holdings]
    tokenIds = (
        db.session.query(UniswapV3Tokens)
        .filter(tuple_(UniswapV3Tokens.position_token_address, UniswapV3Tokens.token_id).in_(token_id_list))
        .all()
    )
    token_id_infos = {}
    for token in tokenIds:
        position_token_address = bytes_to_hex_str(token.position_token_address)
        token_id = token.token_id
        key = (position_token_address, token_id)
        token_id_infos[key] = token

    # Get Token info
    erc20_tokens = set()
    pool_infos = {}
    pools = db.session.query(UniswapV3Pools).filter(UniswapV3Pools.pool_address.in_(unique_pool_addresses)).all()
    for data in pools:
        pool_address = bytes_to_hex_str(data.pool_address)
        pool_infos[pool_address] = data
        erc20_tokens.add(data.token0_address)
        erc20_tokens.add(data.token1_address)

    erc20_datas = db.session.query(Tokens).filter(Tokens.address.in_(erc20_tokens)).all()
    erc20_infos = {}
    token_symbol_list = []
    for data in erc20_datas:
        erc20_infos[bytes_to_hex_str(data.address)] = data
        token_symbol_list.append(data.symbol)

    # Get Token Price
    token_price_map = get_token_price_map_by_symbol_list(list(set(token_symbol_list)))

    result = []
    total_value_usd = 0
    for holding in holdings:
        position_token_address = bytes_to_hex_str(holding.position_token_address)
        token_id = holding.token_id
        pool_address = bytes_to_hex_str(holding.pool_address)
        sqrt_price = pool_price_map[pool_address]
        token_id_info = token_id_infos[(position_token_address, token_id)]
        pool_info = pool_infos[pool_address]
        token0_address = bytes_to_hex_str(pool_info.token0_address)
        token1_address = bytes_to_hex_str(pool_info.token1_address)
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
        token0_value_usd = float(amount0_str) * float(token_price_map.get(token0_info.symbol, 0))
        token1_value_usd = float(amount1_str) * float(token_price_map.get(token1_info.symbol, 0))
        total_value_usd += token0_value_usd
        total_value_usd += token1_value_usd
        result.append(
            {
                "pool_address": pool_address,
                "position_token_address": position_token_address,
                "token_id": str(token_id),
                "block_timestamp": holding.block_timestamp.isoformat("T", "seconds"),
                "token0": {
                    "token0_symbol": token0_info.symbol,
                    "token0_icon_url": token0_info.icon_url,
                    "token0_balance": amount0_str,
                    "token0_value_usd": token0_value_usd,
                },
                "token1": {
                    "token1_symbol": token1_info.symbol,
                    "token1_icon_url": token1_info.icon_url,
                    "token1_balance": amount1_str,
                    "token1_value_usd": token1_value_usd,
                },
            }
        )
    if len(result) == 0:
        return None

    return {
        "data": result,
        "total": len(result),
    }


@uniswap_v3_namespace.route("/v1/aci/<address>/uniswap_v3_liquidity/current_holding")
class UniswapV3WalletLiquidityHolding(Resource):
    def get(self, address):
        address = address.lower()
        address_bytes = hex_str_to_bytes(address)

        # Get all LP holdings
        holdings = (
            db.session.query(UniswapV3TokenCurrentStatus)
            .filter(UniswapV3TokenCurrentStatus.wallet_address == address_bytes)
            .filter(UniswapV3TokenCurrentStatus.liquidity > 0)
            .all()
        )

        # Get Pool Price
        unique_pool_addresses = {holding.pool_address for holding in holdings}
        pool_prices = (
            db.session.query(UniswapV3PoolCurrentPrices)
            .filter(UniswapV3PoolCurrentPrices.pool_address.in_(unique_pool_addresses))
            .all()
        )
        pool_price_map = {}
        for data in pool_prices:
            pool_address = bytes_to_hex_str(data.pool_address)
            pool_price_map[pool_address] = data.sqrt_price_x96

        # Get token id info
        token_id_list = [(holding.position_token_address, holding.token_id) for holding in holdings]
        tokenIds = (
            db.session.query(UniswapV3Tokens)
            .filter(tuple_(UniswapV3Tokens.position_token_address, UniswapV3Tokens.token_id).in_(token_id_list))
            .all()
        )
        token_id_infos = {}
        for token in tokenIds:
            position_token_address = bytes_to_hex_str(token.position_token_address)
            token_id = token.token_id
            key = (position_token_address, token_id)
            token_id_infos[key] = token

        # Get Token info
        erc20_tokens = set()
        pool_infos = {}
        pools = db.session.query(UniswapV3Pools).filter(UniswapV3Pools.pool_address.in_(unique_pool_addresses)).all()
        for data in pools:
            pool_address = bytes_to_hex_str(data.pool_address)
            pool_infos[pool_address] = data
            erc20_tokens.add(data.token0_address)
            erc20_tokens.add(data.token1_address)

        erc20_datas = db.session.query(Tokens).filter(Tokens.address.in_(erc20_tokens)).all()
        erc20_infos = {}
        token_symbol_list = []
        for data in erc20_datas:
            erc20_infos[bytes_to_hex_str(data.address)] = data
            token_symbol_list.append(data.symbol)

        # Get Token Price
        token_price_map = get_token_price_map_by_symbol_list(list(set(token_symbol_list)))

        result = []
        total_value_usd = 0
        for holding in holdings:
            position_token_address = bytes_to_hex_str(holding.position_token_address)
            token_id = holding.token_id
            pool_address = bytes_to_hex_str(holding.pool_address)
            sqrt_price = pool_price_map[pool_address]
            token_id_info = token_id_infos[(position_token_address, token_id)]
            pool_info = pool_infos[pool_address]
            token0_address = bytes_to_hex_str(pool_info.token0_address)
            token1_address = bytes_to_hex_str(pool_info.token1_address)
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
            token0_value_usd = float(amount0_str) * float(token_price_map.get(token0_info.symbol, 0))
            token1_value_usd = float(amount1_str) * float(token_price_map.get(token1_info.symbol, 0))
            total_value_usd += token0_value_usd
            total_value_usd += token1_value_usd
            result.append(
                {
                    "pool_address": pool_address,
                    "position_token_address": position_token_address,
                    "token_id": str(token_id),
                    "block_timestamp": holding.block_timestamp.isoformat("T", "seconds"),
                    "token0": {
                        "token0_symbol": token0_info.symbol,
                        "token0_icon_url": token0_info.icon_url,
                        "token0_balance": amount0_str,
                        "token0_value_usd": token0_value_usd,
                    },
                    "token1": {
                        "token1_symbol": token1_info.symbol,
                        "token1_icon_url": token1_info.icon_url,
                        "token1_balance": amount1_str,
                        "token1_value_usd": token1_value_usd,
                    },
                }
            )

        return {
            "data": result,
            "total": len(result),
            "pool_count": len(unique_pool_addresses),
            "total_value_usd": total_value_usd,
        }


@uniswap_v3_namespace.route("/v1/aci/<address>/uniswap_v3_liquidity/summary")
class UniswapV3WalletLiquidityDetail(Resource):
    def get(self, address):
        address = address.lower()
        address_bytes = hex_str_to_bytes(address)
        first_holding = (
            db.session.query(UniswapV3TokenLiquidityRecords)
            .filter(UniswapV3TokenLiquidityRecords.owner == address_bytes)
            .order_by(UniswapV3TokenLiquidityRecords.block_timestamp)
            .first()
        )
        if not first_holding:
            return {}

        pool_count = (
            db.session.query(UniswapV3TokenLiquidityRecords.pool_address)
            .filter(UniswapV3TokenLiquidityRecords.owner == address_bytes)
            .distinct()
            .count()
        )
        return {
            "first_provide_time": datetime.fromtimestamp(first_holding.block_timestamp).isoformat("T", "seconds"),
            "pool_count": pool_count,
            "total_value_usd": 0,
        }, 200


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


def get_swap_action_type(swap: UniswapV3PoolSwapRecords):
    token0_address_str = bytes_to_hex_str(swap.token0_address)
    token1_address_str = bytes_to_hex_str(swap.token1_address)

    if token0_address_str in STABLE_COINS and token1_address_str in STABLE_COINS:
        return "swap"
    elif token0_address_str in STABLE_COINS:
        return "buy" if swap.amount0 > 0 else "sell"
    elif token1_address_str in STABLE_COINS:
        return "buy" if swap.amount1 > 0 else "sell"
    elif token0_address_str in NATIVE_COINS:
        return "buy" if swap.amount0 > 0 else "sell"
    elif token1_address_str in NATIVE_COINS:
        return "buy" if swap.amount1 > 0 else "sell"

    return "swap"
