from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter
from custom_jobs.staking_fbtc.domain.feature_staked_fbtc_detail import StakedFBTCCurrentStatus, TransferredFBTCCurrentStatus


class FeatureStakedFBTCDetailStatus(HemeraModel):
    __tablename__ = "af_staked_fbtc_current"
    vault_address = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)
    amount = Column(NUMERIC(100))
    changed_amount = Column(NUMERIC(100))
    protocol_id = Column(VARCHAR)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("vault_address", "wallet_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": StakedFBTCCurrentStatus,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_staked_fbtc_current.block_number",
                "converter": general_converter,
            },
            {
                "domain": TransferredFBTCCurrentStatus,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_staked_fbtc_current.block_number",
                "converter": general_converter,
            },
        ]


Index(
    "af_staked_fbtc_current_wallet_block_desc_index",
    desc(FeatureStakedFBTCDetailStatus.wallet_address),
)

Index(
    "af_staked_fbtc_current_protocol_block_desc_index",
    desc(FeatureStakedFBTCDetailStatus.protocol_id),
)
