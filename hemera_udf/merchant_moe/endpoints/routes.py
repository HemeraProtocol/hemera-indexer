from flask_restx import Resource

from hemera.common.models import db
from hemera.common.models.current_token_balances import CurrentTokenBalances
from hemera.common.models.tokens import Tokens
from hemera.common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from hemera_udf.merchant_moe.endpoints import merchant_moe_namespace
from hemera_udf.merchant_moe.models.feature_erc1155_token_current_supply import FeatureErc1155TokenCurrentSupplyStatus
from hemera_udf.merchant_moe.models.feature_merchant_moe_pool import FeatureMerchantMoePools
from hemera_udf.merchant_moe.models.feature_merchant_moe_token_current_bin import (
    FeatureMerchantMoeTokenBinCurrentStatus,
)

Q96 = 2**96


@merchant_moe_namespace.route("/v1/aci/<wallet_address>/merchantmoe/current_holding")
class MerchantMoeWalletHolding(Resource):
    def get(self, wallet_address):
        pool_infos = {}
        pool_tokens = db.session.query(FeatureMerchantMoePools).all()

        tokens = set()
        for data in pool_tokens:
            tokens.add(data.token0_address)
            tokens.add(data.token1_address)
            pool_infos[bytes_to_hex_str(data.token_address)] = {
                "getTokenX": bytes_to_hex_str(data.token0_address),
                "getTokenY": bytes_to_hex_str(data.token1_address),
            }
        wallet_address = wallet_address.lower()
        address_bytes = hex_str_to_bytes(wallet_address)
        holdings = (
            db.session.query(CurrentTokenBalances)
            .filter(
                CurrentTokenBalances.address == address_bytes,
                CurrentTokenBalances.token_type == "ERC1155",
                CurrentTokenBalances.balance > 0,
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
            db.session.query(FeatureMerchantMoeTokenBinCurrentStatus)
            .filter(FeatureMerchantMoeTokenBinCurrentStatus.token_address.in_(unique_token_addresses))
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
            erc20_infos[bytes_to_hex_str(data.address)] = data

        result = []
        token_total_amount = {}
        for holding in holdings:
            nft_address = bytes_to_hex_str(holding.token_address)
            if nft_address not in pool_infos:
                continue
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

            amount0_human = token0_balance / 10**token0_info.decimals
            amount1_human = token1_balance / 10**token1_info.decimals
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
