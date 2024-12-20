from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, JSONB, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.day_mining.domains import CurrentTraitsActiveness


class CurrentTraitsActivenessModel(HemeraModel):
    __tablename__ = "current_traits_activeness"
    block_number = Column(BIGINT, primary_key=True)
    address = Column(BYTEA, primary_key=True)

    value = Column(JSONB)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("address", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": CurrentTraitsActiveness,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]