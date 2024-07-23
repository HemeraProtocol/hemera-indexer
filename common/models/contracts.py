from datetime import datetime
from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, BIGINT, TIMESTAMP, BOOLEAN, JSONB, VARCHAR

from common.models import HemeraModel


class Contracts(HemeraModel):
    __tablename__ = 'contracts'

    address = Column(BYTEA, primary_key=True)
    name = Column(VARCHAR)
    contract_creator = Column(BYTEA)
    creation_code = Column(BYTEA)
    deployed_code = Column(BYTEA)

    block_number = Column(BIGINT)
    block_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)
    transaction_index = Column(INTEGER)
    transaction_hash = Column(BYTEA)

    official_website = Column(VARCHAR)
    description = Column(VARCHAR)
    email = Column(VARCHAR)
    social_list = Column(JSONB)
    is_verified = Column(BOOLEAN)
    is_proxy = Column(BOOLEAN)
    implementation_contract = Column(BYTEA)
    verified_implementation_contract = Column(BYTEA)
    proxy_standard = Column(VARCHAR)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)
