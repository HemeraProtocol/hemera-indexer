from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.merchant_moe.domains import MerchantMoeErc1155TokenHolding


class FeatureErc1155TokenHoldings(HemeraModel):
    __tablename__ = "af_erc1155_token_holdings_hist"
    position_token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)

    balance = Column(NUMERIC(100))

    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (
        PrimaryKeyConstraint("position_token_address", "token_id", "wallet_address", "block_timestamp", "block_number"),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": MerchantMoeErc1155TokenHolding,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "feature_erc1155_token_holding_token_wallet_block_desc_index",
    desc(FeatureErc1155TokenHoldings.position_token_address),
    desc(FeatureErc1155TokenHoldings.wallet_address),
    desc(FeatureErc1155TokenHoldings.block_number),
)

Index(
    "feature_erc1155_token_holding_token_block_desc_index",
    desc(FeatureErc1155TokenHoldings.position_token_address),
    desc(FeatureErc1155TokenHoldings.block_timestamp),
)
