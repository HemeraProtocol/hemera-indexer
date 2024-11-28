from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, JSONB, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.domains.all_features_value_record import (
    AllFeatureValueRecordBlueChipHolders,
    AllFeatureValueRecordTraitsActiveness,
    AllFeatureValueRecordUniswapV2Info,
    AllFeatureValueRecordUniswapV3Pool,
    AllFeatureValueRecordUniswapV3Token,
)


class AllFeatureValueRecords(HemeraModel):
    __tablename__ = "all_feature_value_records"

    feature_id = Column(NUMERIC(100), primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    address = Column(BYTEA, primary_key=True)

    value = Column(JSONB)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("block_number", "feature_id", "address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AllFeatureValueRecordUniswapV3Pool,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": AllFeatureValueRecordUniswapV3Token,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": AllFeatureValueRecordUniswapV2Info,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": AllFeatureValueRecordTraitsActiveness,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": AllFeatureValueRecordBlueChipHolders,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


Index(
    "all_feature_value_records_feature_block_index",
    AllFeatureValueRecords.feature_id,
    desc(AllFeatureValueRecords.block_number),
)
