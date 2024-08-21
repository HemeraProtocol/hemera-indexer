from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureErc1155TokenCurrentHoldings(HemeraModel):
    __tablename__ = "feature_erc1155_token_current_holdings"
    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)

    balance = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("token_address", "token_id", "wallet_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "MerchantMoeErc1155TokenCurrentHolding",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > feature_erc1155_token_current_holdings.block_number",
                "converter": general_converter,
            }
        ]


Index(
    "feature_erc1155_token_current_holdings_token_block_desc_index",
    desc(FeatureErc1155TokenCurrentHoldings.token_address),
    desc(FeatureErc1155TokenCurrentHoldings.block_timestamp),
)

Index(
    "feature_erc1155_token_current_holdings_wallet_block_desc_index",
    desc(FeatureErc1155TokenCurrentHoldings.wallet_address),
    desc(FeatureErc1155TokenCurrentHoldings.block_timestamp),
)
