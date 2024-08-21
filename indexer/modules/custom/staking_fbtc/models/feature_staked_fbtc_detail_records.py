from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class FeatureStakedFBTCDetailRecords(HemeraModel):
    __tablename__ = "feature_staked_fbtc_detail_records"
    contract_address = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)
    log_index = Column(BIGINT, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)
    amount = Column(NUMERIC(100))
    protocol_id = Column(VARCHAR)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (
        PrimaryKeyConstraint("contract_address", "wallet_address", "block_timestamp", "block_number", "log_index"),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "StakedFBTCDetail",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "feature_staked_fbtc_detail_records_wallet_block_desc_index",
    desc(FeatureStakedFBTCDetailRecords.wallet_address),
    desc(FeatureStakedFBTCDetailRecords.block_timestamp),
)

Index(
    "feature_staked_fbtc_detail_records_protocol_block_desc_index",
    desc(FeatureStakedFBTCDetailRecords.protocol_id),
    desc(FeatureStakedFBTCDetailRecords.block_timestamp),
)
