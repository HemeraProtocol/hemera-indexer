from flask_restx import Resource
from sqlalchemy import func

from common.models import db
from common.models.tokens import Tokens
from common.utils.format_utils import bytes_to_hex_str, hex_str_to_bytes
from indexer.modules.custom.staking_fbtc.endpoints import staking_namespace
from indexer.modules.custom.staking_fbtc.models.feature_staked_fbtc_detail_records import FeatureStakedFBTCDetailRecords

FBTC_ADDRESS = "0xc96de26018a54d51c097160568752c4e3bd6c364"


@staking_namespace.route("/v1/aci/<wallet_address>/staking/current_holding")
class StakingWalletHolding(Resource):
    def get(self, wallet_address):
        wallet_address = wallet_address.lower()
        address_bytes = hex_str_to_bytes(wallet_address)
        results = (
            db.session.query(
                FeatureStakedFBTCDetailRecords.vault_address,
                func.max(FeatureStakedFBTCDetailRecords.protocol_id).label("protocol_id"),
                func.sum(FeatureStakedFBTCDetailRecords.amount).label("total_amount"),
            )
            .filter(FeatureStakedFBTCDetailRecords.wallet_address == address_bytes)
            .group_by(FeatureStakedFBTCDetailRecords.contract_address)
            .all()
        )

        erc20_data = db.session.query(Tokens).filter(Tokens.address == hex_str_to_bytes(FBTC_ADDRESS)).first()
        erc20_infos = {}
        result = []
        for holding in results:
            contract_address = bytes_to_hex_str(holding.vault_address)
            total_amount = holding.total_amount
            protocol_id = holding.protocol_id
            token_amount = total_amount / (10**erc20_data.decimals)
            result.append(
                {
                    "protocol_id": protocol_id,
                    "vault_address": contract_address,
                    "total_amount": str(total_amount),
                    "token_amount": str(token_amount),
                }
            )

        return result, 200
