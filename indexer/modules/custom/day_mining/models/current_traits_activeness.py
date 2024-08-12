from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, JSONB, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class CurrentTraitsActivenessModel(HemeraModel):
    __tablename__ = "current_traits_activeness"
    block_number = Column(BIGINT, primary_key=True)
    address = Column(BYTEA, primary_key=True)

    value = Column(JSONB)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "CurrentTraitsActiveness",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
