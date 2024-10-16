from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, JSONB, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class StoryLicenseAttach(HemeraModel):
    __tablename__ = "story_license_attach"

    caller = Column(BYTEA, primary_key=True)
    ip_id = Column(BYTEA, primary_key=True)
    license_template = Column(BYTEA, primary_key=True)
    license_terms_id = Column(BIGINT)
    block_number = Column(BIGINT)
    transaction_hash = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("caller", "ip_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "StoryLicenseAttach",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


Index(
    "story_license_attach_id_index",
    StoryLicenseAttach.caller,
    StoryLicenseAttach.ip_id,
)