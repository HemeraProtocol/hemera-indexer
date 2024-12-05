from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.modules.custom.staking_fbtc.domain.feature_staked_fbtc_detail import (
    StakedFBTCDetail,
    TransferredFBTCDetail,
)


class FeatureStakedFBTCDetailRecords(HemeraModel):
    __tablename__ = "af_staked_fbtc_detail_hist"
    vault_address = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA, primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(BIGINT, primary_key=True)
    amount = Column(NUMERIC(100))
    changed_amount = Column(NUMERIC(100))
    protocol_id = Column(VARCHAR)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("vault_address", "wallet_address", "block_timestamp", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": StakedFBTCDetail,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": TransferredFBTCDetail,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


Index(
    "af_staked_fbtc_detail_hist_wallet_block_desc_index",
    desc(FeatureStakedFBTCDetailRecords.wallet_address),
    desc(FeatureStakedFBTCDetailRecords.block_timestamp),
)

Index(
    "af_staked_fbtc_detail_hist_protocol_block_desc_index",
    desc(FeatureStakedFBTCDetailRecords.protocol_id),
    desc(FeatureStakedFBTCDetailRecords.block_timestamp),
)
