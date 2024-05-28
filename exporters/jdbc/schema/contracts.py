from datetime import datetime
from sqlalchemy import Column, VARCHAR
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, INTEGER, BIGINT, TIMESTAMP, BOOLEAN, TEXT, JSONB
from exporters.jdbc.schema import Base


class Contracts(Base):
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
    implementation_contract = Column(BOOLEAN)
    verified_implementation_contract = Column(BOOLEAN)
    proxy_standard = Column(BOOLEAN)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP)
