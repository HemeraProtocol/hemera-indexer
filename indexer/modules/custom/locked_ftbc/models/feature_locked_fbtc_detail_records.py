from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class FeatureLockedFBTCDetailRecords(HemeraModel):
    __tablename__ = "feature_locked_fbtc_detail_records"
    contract_address = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)
    log_index = Column(BIGINT, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)
    minter = Column(BYTEA)
    received_amount = Column(NUMERIC(100))
    fee = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (
        PrimaryKeyConstraint("contract_address", "wallet_address", "block_timestamp", "block_number", "log_index"),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "LockedFBTCDetail",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "feature_locked_fbtc_detail_records_wallet_block_desc_index",
    desc(FeatureLockedFBTCDetailRecords.wallet_address),
    desc(FeatureLockedFBTCDetailRecords.block_timestamp),
)

Index(
    "feature_locked_fbtc_detail_records_contract_block_desc_index",
    desc(FeatureLockedFBTCDetailRecords.contract_address),
    desc(FeatureLockedFBTCDetailRecords.block_timestamp),
)
