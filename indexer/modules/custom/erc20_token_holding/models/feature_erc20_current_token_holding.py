from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class FeatureErc20CurrentTokenHoldings(HemeraModel):
    __tablename__ = "af_erc20_token_holding_current"

    token_address = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)

    balance = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("wallet_address", "token_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "Erc20CurrentTokenHolding",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_erc20_token_holding_current.block_number",
                "converter": general_converter,
            }
        ]


Index(
    "af_erc20_token_holding_current_token_balance_index",
    FeatureErc20CurrentTokenHoldings.token_address,
    desc(FeatureErc20CurrentTokenHoldings.balance),
)
