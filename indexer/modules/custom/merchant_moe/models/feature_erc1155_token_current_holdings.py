from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.modules.custom.merchant_moe.domains.erc1155_token_holding import MerchantMoeErc1155TokenCurrentHolding


class FeatureErc1155TokenCurrentHoldings(HemeraModel):
    __tablename__ = "af_erc1155_token_holdings_current"
    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)

    balance = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("position_token_address", "token_id", "wallet_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": MerchantMoeErc1155TokenCurrentHolding,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_erc1155_token_holdings_current.block_number",
                "converter": general_converter,
            }
        ]


Index(
    "af_erc1155_token_holdings_current_token_block_desc_index",
    desc(FeatureErc1155TokenCurrentHoldings.position_token_address),
    desc(FeatureErc1155TokenCurrentHoldings.block_timestamp),
)

Index(
    "af_erc1155_token_holdings_current_wallet_block_desc_index",
    desc(FeatureErc1155TokenCurrentHoldings.wallet_address),
    desc(FeatureErc1155TokenCurrentHoldings.block_timestamp),
)
