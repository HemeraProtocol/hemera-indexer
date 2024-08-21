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
from indexer.modules.custom.staking_fbtc.models.feature_staked_fbtc_detail_records import FeatureStakedFBTCDetailRecords

FBTC_ADDRESS = "0xc96de26018a54d51c097160568752c4e3bd6c364"


@custom_namespace.route("/v1/staked_fbtc/<wallet_address>")
class StakedFBTC(Resource):
    def get(self, wallet_address):
        wallet_address = wallet_address.lower()
        address_bytes = bytes.fromhex(wallet_address[2:])
        results = (
            db.session.query(
                FeatureStakedFBTCDetailRecords.contract_address,
                func.max(FeatureStakedFBTCDetailRecords.protocol_id).label("protocol_id"),
                func.sum(FeatureStakedFBTCDetailRecords.amount).label("total_amount"),
            )
            .filter(FeatureStakedFBTCDetailRecords.wallet_address == address_bytes)
            .group_by(FeatureStakedFBTCDetailRecords.contract_address)
            .all()
        )

        erc20_data = db.session.query(Tokens).filter(Tokens.address == bytes.fromhex(FBTC_ADDRESS[2:])).first()
        erc20_infos = {}
        result = []
        for holding in results:
            contract_address = "0x" + holding.contract_address.hex()
            total_amount = holding.total_amount
            protocol_id = holding.protocol_id
            token_amount = total_amount / (10 ** erc20_data.decimals)
            result.append(
                {
                    "protocol_id": protocol_id,
                    "contract_address": contract_address,
                    "total_amount": str(total_amount),
                    "token_amount": str(token_amount),
                }
            )

        return result, 200
