from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, JSONB, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class StoryLicenseTokenMint(HemeraModel):
    __tablename__ = "story_license_token_mint"

    caller = Column(BYTEA, primary_key=True)
    licensor_ip_id = Column(BYTEA, primary_key=True)
    license_template = Column(BYTEA, primary_key=True)
    license_terms_id = Column(BIGINT)
    amount = Column(BIGINT)
    receiver = Column(BYTEA, primary_key=True)
    start_license_token_id = Column(NUMERIC(100), primary_key=True)
    block_number = Column(BIGINT)
    transaction_hash = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("caller", "license_terms_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "StoryLicenseTokenMint",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


Index(
    "story_license_attach_id_index",
    StoryLicenseTokenMint.caller,
    StoryLicenseTokenMint.license_terms_id,
)
