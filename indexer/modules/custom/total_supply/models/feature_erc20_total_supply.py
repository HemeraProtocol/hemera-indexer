from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureErc20TotalSupply(HemeraModel):
    __tablename__ = "feature_erc20_total_supply"
    chain_id = Column(BIGINT, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)

    total_supply = Column(BIGINT)

    called_block_number = Column(BIGINT)
    called_block_timestamp = Column(BIGINT)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("chain_id", "token_address", "called_block_timestamp"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "Erc20TotalSupply",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "feature_erc20_total_supply_token_block_desc_index",
    desc(FeatureErc20TotalSupply.token_address),
    desc(FeatureErc20TotalSupply.called_block_number),
    desc(FeatureErc20TotalSupply.chain_id),
)
