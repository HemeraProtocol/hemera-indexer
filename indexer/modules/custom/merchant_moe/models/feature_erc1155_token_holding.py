from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureErc1155TokenHoldings(HemeraModel):
    __tablename__ = "feature_erc1155_token_holdings"
    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)

    balance = Column(NUMERIC(100))

    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (
        PrimaryKeyConstraint("token_address", "token_id", "wallet_address", "block_timestamp", "block_number"),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "MerchantMoeErc1155TokenHolding",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "feature_erc1155_token_holding_token_wallet_block_desc_index",
    desc(FeatureErc1155TokenHoldings.token_address),
    desc(FeatureErc1155TokenHoldings.wallet_address),
    desc(FeatureErc1155TokenHoldings.block_number),
)

Index(
    "feature_erc1155_token_holding_token_block_desc_index",
    desc(FeatureErc1155TokenHoldings.token_address),
    desc(FeatureErc1155TokenHoldings.block_timestamp),
)
