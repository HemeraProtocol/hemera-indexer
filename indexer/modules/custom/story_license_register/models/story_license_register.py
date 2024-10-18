from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, JSONB, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class StoryLicenseRegister(HemeraModel):
    __tablename__ = "story_license_register"

    license_terms_id = Column(NUMERIC(100), primary_key=True)
    license_template = Column(BYTEA, primary_key=True)
    transferable = Column(BOOLEAN, primary_key=True)
    royalty_policy = Column(BYTEA, primary_key=True)
    default_minting_fee = Column(NUMERIC(100), primary_key=True)
    expiration = Column(NUMERIC(100), primary_key=True)
    commercial_use = Column(BOOLEAN, primary_key=True)
    commercial_attribution = Column(BOOLEAN, primary_key=True)
    commercializer_checker = Column(BYTEA, primary_key=True)
    commercializer_checker_data = Column(BYTEA, primary_key=True)
    commercial_rev_share = Column(NUMERIC(100), primary_key=True)
    commercial_rev_ceiling = Column(NUMERIC(100), primary_key=True)
    derivatives_allowed = Column(BOOLEAN, primary_key=True)
    derivatives_attribution = Column(BOOLEAN, primary_key=True)
    derivatives_approval = Column(BOOLEAN, primary_key=True)
    derivatives_reciprocal = Column(BOOLEAN, primary_key=True)
    derivative_rev_ceiling = Column(NUMERIC(100), primary_key=True)
    currency = Column(BYTEA, primary_key=True)
    uri = Column(VARCHAR, primary_key=True)
    contract_address = Column(BYTEA)
    block_number = Column(BIGINT)
    transaction_hash = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("license_terms_id", "license_template"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "StoryLicenseRegister",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


Index(
    "story_id_licenseTemplate_index",
    StoryLicenseRegister.license_terms_id,
    StoryLicenseRegister.license_template,
)
