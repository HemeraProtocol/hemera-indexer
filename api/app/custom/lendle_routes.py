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

VOUCHER_DICT = {
    "0xdef3542bb1b2969c1966dd91ebc504f4b37462fe": 1,
    "0x874712c653aaaa7cfb201317f46e00238c2649bb": -1,
    "0x08fc23af290d538647aa2836c5b3cf2fb3313759": -1,
}
FBTC_ADDRESS = "0xc96de26018a54d51c097160568752c4e3bd6c364"


# for mantle
@custom_namespace.route("/v1/lendle/<wallet_address>")
class DodoFBTC(Resource):
    def get(self, wallet_address):
        wallet_address = wallet_address.lower()
        address_bytes = bytes.fromhex(wallet_address[2:])
        voucher_bytes_addresses = set()
        for data in VOUCHER_DICT.keys():
            voucher_bytes_addresses.add(bytes.fromhex(data[2:]))
        balance_of_entities = (
            db.session.query(CurrentTokenBalances)
            .filter(
                CurrentTokenBalances.address == address_bytes,
                CurrentTokenBalances.token_address.in_(voucher_bytes_addresses),
            )
            .all()
        )
        holding_details = {}
        for data in balance_of_entities:
            wallet_address = "0x" + data.address.hex()
            contract_address = "0x" + data.token_address.hex()
            data.address = wallet_address
            data.token_address = contract_address
            holding_details[contract_address] = data
        if not balance_of_entities:
            return {"message": "no lendle holding"}, 200

        voucher_bytes_addresses.add(bytes.fromhex(FBTC_ADDRESS[2:]))
        erc20_datas = db.session.query(Tokens).filter(Tokens.address.in_(voucher_bytes_addresses)).all()
        erc20_infos = {}
        for data in erc20_datas:
            erc20_infos["0x" + data.address.hex()] = data
        result = []
        fbtc_info = erc20_infos[FBTC_ADDRESS]
        for key, data in holding_details.items():
            contract_address = data.token_address
            token_info = erc20_infos[contract_address]
            result.append(
                {
                    "contract_address": key,
                    "token_balance": str(data.balance / (10**token_info.decimals) * VOUCHER_DICT[contract_address]),
                    "token_symbol": fbtc_info.symbol,
                    "token_address": FBTC_ADDRESS,
                }
            )
        return result, 200
