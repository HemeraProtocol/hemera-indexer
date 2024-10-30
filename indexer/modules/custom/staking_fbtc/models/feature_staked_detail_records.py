from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class FeatureStakedTransferDetailRecords(HemeraModel):
    __tablename__ = "feature_staked_transfer_detail_records"
    contract_address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)
    block_transfer_value = Column(NUMERIC(100))
    block_cumulative_value = Column(NUMERIC(100))
    protocol_id = Column(VARCHAR)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("contract_address", "wallet_address", "token_address", "block_timestamp", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "TransferredStakedDetail",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]