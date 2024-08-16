from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureErc1155TokenHolding(HemeraModel):
    __tablename__ = "feature_erc1155_token_holding"
    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)

    balance = Column(NUMERIC(100))

    called_block_number = Column(BIGINT, primary_key=True)
    called_block_timestamp = Column(BIGINT, primary_key=True)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (
        PrimaryKeyConstraint(
            "token_address", "token_id", "wallet_address", "called_block_timestamp", "called_block_number"
        ),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "Erc1155TokenHolding",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "feature_erc1155_token_holding_token_wallet_block_desc_index",
    desc(FeatureErc1155TokenHolding.token_address),
    desc(FeatureErc1155TokenHolding.wallet_address),
    desc(FeatureErc1155TokenHolding.called_block_number),
)

Index(
    "feature_erc1155_token_holding_token_block_desc_index",
    desc(FeatureErc1155TokenHolding.token_address),
    desc(FeatureErc1155TokenHolding.called_block_timestamp),
)
