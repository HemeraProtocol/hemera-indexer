from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, JSONB, NUMERIC, TIMESTAMP, VARCHAR, ARRAY, INTEGER

from common.models import HemeraModel, general_converter


class StoryDerivativeRegister(HemeraModel):
    __tablename__ = "story_derivative_register"

    caller = Column(BYTEA, primary_key=True)
    child_ip_id = Column(BYTEA, primary_key=True)
    license_token_ids = Column(ARRAY(INTEGER))
    parent_ip_ids = Column(ARRAY(BYTEA))
    license_terms_id = Column(ARRAY(INTEGER))

    license_template = Column(BYTEA)
    block_number = Column(BIGINT)
    transaction_hash = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("caller", "child_ip_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "StoryDerivativeRegister",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


Index(
    "story_derivative_register_id_index",
    StoryDerivativeRegister.caller,
    StoryDerivativeRegister.child_ip_id,
)