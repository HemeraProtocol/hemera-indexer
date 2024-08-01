from datetime import datetime
from sqlalchemy import Column, PrimaryKeyConstraint, Index, desc, func
from sqlalchemy.dialects.postgresql import BYTEA, BIGINT, TIMESTAMP, NUMERIC, BOOLEAN, VARCHAR, JSONB

from common.models import db, HemeraModel, general_converter


class AllFeatureValueRecords(HemeraModel):
    __tablename__ = 'all_feature_value_records'

    feature_id = Column(NUMERIC(100), primary_key=True)
    block_number = Column(BIGINT, primary_key=True)
    address = Column(BYTEA, primary_key=True)

    value = Column(JSONB)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (
        PrimaryKeyConstraint('block_number', 'feature_id', 'address'),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                'domain': 'AllFeatureValueRecordUniswapV3Pool',
                'conflict_do_update': True,
                'update_strategy': None,
                'converter': general_converter,
            },
            {
                'domain': 'AllFeatureValueRecordUniswapV3Token',
                'conflict_do_update': True,
                'update_strategy': None,
                'converter': general_converter,
            }
        ]


Index('all_feature_value_records_feature_block_index',
      AllFeatureValueRecords.feature_id, desc(AllFeatureValueRecords.block_number))
