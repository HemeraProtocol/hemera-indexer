from sqlalchemy import Column, Index, desc, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC, TEXT, TIMESTAMP

from common.models import HemeraModel, general_converter
from custom_jobs.address_index.domains.address_contract_operation import AddressContractOperation


class AddressContractOperations(HemeraModel):
    __tablename__ = "address_contract_operations"

    address = Column(BYTEA, primary_key=True)
    trace_from_address = Column(BYTEA)
    contract_address = Column(BYTEA)
    trace_id = Column(TEXT, primary_key=True)
    block_number = Column(INTEGER, primary_key=True)
    transaction_index = Column(INTEGER, primary_key=True)
    transaction_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP, primary_key=True)
    block_hash = Column(BYTEA)
    error = Column(TEXT)
    status = Column(INTEGER)
    creation_code = Column(BYTEA)
    deployed_code = Column(BYTEA)
    gas = Column(NUMERIC(100))
    gas_used = Column(NUMERIC(100))
    trace_type = Column(TEXT)
    call_type = Column(TEXT)
    transaction_receipt_status = Column(INTEGER)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AddressContractOperation,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "address_contract_operations_address_block_tn_t_idx",
    AddressContractOperations.address,
    desc(AddressContractOperations.block_timestamp),
    desc(AddressContractOperations.block_number),
    desc(AddressContractOperations.transaction_index),
)
