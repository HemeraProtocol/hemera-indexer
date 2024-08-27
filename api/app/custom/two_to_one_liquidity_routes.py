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
from common.models.current_token_balances import CurrentTokenBalances
from common.models.tokens import Tokens
from common.utils.exception_control import APIError
from common.utils.format_utils import as_dict, format_to_dict, format_value_for_json, row_to_dict
from indexer.modules.custom.total_supply.models.feature_erc20_current_total_supply import (
    FeatureErc20CurrentTotalSupplyRecords,
)

_BASE_TOKEN_ = (
    "0xc96de26018a54d51c097160568752c4e3bd6c364".lower()
)  # bsc:0xC96dE26018A54D51c097160568752c4E3BD6C364; mantle: 0xC96dE26018A54D51c097160568752c4E3BD6C364
_QUOTE_TOKEN_ = (
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599".lower()
)  # bsc:0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c; mantle: 0xCAbAE6f6Ea1ecaB08Ad02fE02ce9A44F09aebfA2
DODO_ADDRESS = "0xD39DFbfBA9E7eccd813918FfbDa10B783EA3b3C6".lower()
_MT_FEE_BASE_ = 30373474  # bsc: 1206887;mantle: 983144
_MT_FEE_QUOTE_ = 14587260  # bsc: 34932430381550568; mantle : 307568


# for ethereum
@custom_namespace.route("/v1/dodo/<wallet_address>")
class DodoFBTC(Resource):
    def get(self, wallet_address):
        wallet_address = wallet_address.lower()
        address_bytes = bytes.fromhex(wallet_address[2:])
        dodo_address_bytes = bytes.fromhex(DODO_ADDRESS[2:])
        dodo_balance_of_entity = (
            db.session.query(CurrentTokenBalances)
            .filter(
                CurrentTokenBalances.address == address_bytes, CurrentTokenBalances.token_address == dodo_address_bytes
            )
            .first()
        )
        if not dodo_balance_of_entity or dodo_balance_of_entity.balance == 0:
            return {"message": "no dodo holding"}, 200

        current_total_supply = (
            db.session.query(FeatureErc20CurrentTotalSupplyRecords)
            .filter(FeatureErc20CurrentTotalSupplyRecords.token_address == dodo_address_bytes)
            .first()
        )
        if not current_total_supply or current_total_supply.total_supply == 0:
            return {"message": "no dodo totalSupply"}, 200
        base_balance_entity = (
            db.session.query(CurrentTokenBalances)
            .filter(
                CurrentTokenBalances.address == dodo_address_bytes,
                CurrentTokenBalances.token_address == bytes.fromhex(_BASE_TOKEN_[2:]),
            )
            .first()
        )
        base_balance = base_balance_entity.balance - _MT_FEE_BASE_
        quote_balance_entity = (
            db.session.query(CurrentTokenBalances)
            .filter(
                CurrentTokenBalances.address == dodo_address_bytes,
                CurrentTokenBalances.token_address == bytes.fromhex(_QUOTE_TOKEN_[2:]),
            )
            .first()
        )
        quote_balance = quote_balance_entity.balance - _MT_FEE_QUOTE_
        rate = dodo_balance_of_entity.balance / current_total_supply.total_supply
        erc20_tokens = set()
        erc20_tokens.add(bytes.fromhex(_BASE_TOKEN_[2:]))
        erc20_tokens.add(bytes.fromhex(_QUOTE_TOKEN_[2:]))
        erc20_datas = db.session.query(Tokens).filter(Tokens.address.in_(erc20_tokens)).all()
        erc20_infos = {}
        for data in erc20_datas:
            erc20_infos["0x" + data.address.hex()] = data
        return {
            "balance_of": str(dodo_balance_of_entity.balance),
            "total_supply": str(current_total_supply.total_supply),
            "base_info": {
                "token_address": _BASE_TOKEN_,
                "token_symbol": erc20_infos[_BASE_TOKEN_].symbol,
                "token_balance": str(rate * base_balance / 10 ** erc20_infos[_BASE_TOKEN_].decimals),
            },
            "quote_info": {
                "token_address": _QUOTE_TOKEN_,
                "token_symbol": erc20_infos[_QUOTE_TOKEN_].symbol,
                "token_balance": str(rate * quote_balance / 10 ** erc20_infos[_QUOTE_TOKEN_].decimals),
            },
        }, 200
