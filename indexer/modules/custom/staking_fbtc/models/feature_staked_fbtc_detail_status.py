from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class FeatureStakedFBTCDetailStatus(HemeraModel):
    __tablename__ = "feature_staked_fbtc_status"
    contract_address = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)
    amount = Column(NUMERIC(100))
    protocol_id = Column(VARCHAR)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("contract_address", "wallet_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "StakedFBTCCurrentStatus",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > feature_staked_fbtc_status.block_number",
                "converter": general_converter,
            },
            {
                "domain": "TransferredFBTCCurrentStatus",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > feature_staked_fbtc_status.block_number",
                "converter": general_converter,
            },
        ]


Index(
    "feature_staked_fbtc_status_wallet_block_desc_index",
    desc(FeatureStakedFBTCDetailStatus.wallet_address),
)

Index(
    "feature_staked_fbtc_status_protocol_block_desc_index",
    desc(FeatureStakedFBTCDetailStatus.protocol_id),
)
