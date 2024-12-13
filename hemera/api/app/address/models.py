from sqlalchemy import Column, Integer
from sqlalchemy.dialects.postgresql import BOOLEAN, BYTEA, INTEGER, NUMERIC, TEXT, TIMESTAMP

from hemera.common.models import HemeraModel


class AddressBaseProfile(HemeraModel):
    __tablename__ = "af_base_profile"

    address = Column(BYTEA, primary_key=True, nullable=False)
    init_funding_from_address = Column(BYTEA)
    init_funding_value = Column(NUMERIC(100))
    init_funding_transaction_hash = Column(BYTEA)
    init_funding_block_timestamp = Column(TIMESTAMP)
    init_block_hash = Column(BYTEA)
    init_block_number = Column(INTEGER)
    creation_code = Column(BYTEA)
    deployed_code = Column(BYTEA)
    deployed_block_timestamp = Column(TIMESTAMP)
    deployed_block_number = Column(INTEGER)
    deployed_block_hash = Column(BYTEA)
    deployed_transaction_hash = Column(BYTEA)
    deployed_internal_transaction_from_address = Column(BYTEA)
    deployed_transaction_from_address = Column(BYTEA)
    deployed_trace_id = Column(TEXT)
    is_contract = Column(BOOLEAN)
    first_transaction_hash = Column(BYTEA)
    first_block_hash = Column(BYTEA)
    first_block_number = Column(INTEGER)
    first_block_timestamp = Column(TIMESTAMP)
    first_trace_id = Column(TEXT)
    first_is_from_address = Column(BOOLEAN)
    first_trace_type = Column(TEXT)
    first_call_type = Column(TEXT)


class ScheduledMetadata(HemeraModel):
    __tablename__ = "af_base_na_scheduled_metadata"

    id = Column(Integer, primary_key=True)
    dag_id = Column(TEXT)
    execution_date = Column(TIMESTAMP)
    last_data_timestamp = Column(TIMESTAMP)
