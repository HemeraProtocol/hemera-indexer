from typing import Any, Dict, List, Optional, Union

from flask_restx import Resource

from hemera.api.app.address.features import register_feature
from hemera.api.app.cache import cache
from hemera.common.models import db
from hemera.common.utils.format_utils import as_dict, bytes_to_hex_str, hex_str_to_bytes
from hemera_udf.init_capital.endpoints import init_capital_namespace
from hemera_udf.init_capital.models.init_capital_models import (
    InitCapitalPoolCurrent,
    InitCapitalPositionCurrent,
    InitCapitalRecords,
)

VIRTUAL_SHARES = 10**8
VIRTUAL_ASSETS = 1


@register_feature("init_capital", "value")
def get_address_positions(address: Union[str, bytes]):
    address_bytes = hex_str_to_bytes(address) if isinstance(address, str) else address

    positions = (
        db.session.query(InitCapitalPositionCurrent)
        .filter(InitCapitalPositionCurrent.viewer_address == address_bytes)
        .all()
    )

    collaterals_token_map = {}
    borrow_token_map = {}
    token_bytes_list = []
    position_list = []
    for position in positions:
        if position.collaterals:
            for collateral in position.collaterals:
                if collateral["amount"] != 0:
                    if collateral["token_address"] not in collaterals_token_map:
                        collaterals_token_map[collateral["token_address"]] = {"amount": 0}

                    collaterals_token_map[collateral["token_address"]]["amount"] += collateral["amount"]
                    token_bytes_list.append(hex_str_to_bytes(collateral["token_address"]))
        if position.borrows:
            for borrow in position.borrows:
                if borrow["share"] != 0:
                    if borrow["token_address"] not in borrow_token_map:
                        borrow_token_map[borrow["token_address"]] = {
                            "amount": 0,
                            "share": 0,
                        }
                    borrow_token_map[borrow["token_address"]]["amount"] += borrow["amount"]
                    borrow_token_map[borrow["token_address"]]["share"] += borrow["share"]
                    token_bytes_list.append(hex_str_to_bytes(borrow["token_address"]))

        position_list.append(
            {
                "position_id": str(position.position_id),
                "collaterals": position.collaterals,
                "borrows": position.borrows,
                "block_number": position.block_number,
            }
        )

    token_infos = (
        db.session.query(InitCapitalPoolCurrent)
        .filter(InitCapitalPoolCurrent.token_address.in_(token_bytes_list))
        .all()
    )
    token_info_map = {}
    for token in token_infos:
        token_info_map[bytes_to_hex_str(token.token_address)] = token

    for token in collaterals_token_map:
        collateral = collaterals_token_map[token]
        collateral["true_amount"] = str(
            collateral["amount"]
            * (token_info_map[token].total_asset + VIRTUAL_ASSETS)
            / (token_info_map[token].total_supply + VIRTUAL_SHARES)
        )

    for token in borrow_token_map:
        borrow = borrow_token_map[token]
        borrow["true_amount"] = str(
            borrow["share"] * token_info_map[token].total_debt / token_info_map[token].total_debt_share
        )

    return {
        "posistions": position_list,
        "collaterals": collaterals_token_map,
        "borrows": borrow_token_map,
    }


@init_capital_namespace.route("/v1/aci/<address>/init_capital/profile")
class ACIOpenseaProfile(Resource):
    def get(self, address):
        address = address.lower()
        return get_address_positions(address)
