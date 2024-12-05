from sqlalchemy import Column, Index, desc, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC, SMALLINT, TEXT, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.modules.custom.address_index.domain.address_internal_transaction import AddressInternalTransaction


class AddressInternalTransactions(HemeraModel):
    __tablename__ = "address_internal_transactions"

    address = Column(BYTEA, primary_key=True)
    trace_id = Column(TEXT, primary_key=True)
    block_number = Column(INTEGER, primary_key=True)
    transaction_index = Column(INTEGER, primary_key=True)
    transaction_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP, primary_key=True)
    block_hash = Column(BYTEA)
    error = Column(TEXT)
    status = Column(INTEGER)
    input_method = Column(TEXT)
    value = Column(NUMERIC(100))
    gas = Column(NUMERIC(100))
    gas_used = Column(NUMERIC(100))
    trace_type = Column(TEXT)
    call_type = Column(TEXT)
    txn_type = Column(SMALLINT)
    related_address = Column(BYTEA)
    transaction_receipt_status = Column(INTEGER)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AddressInternalTransaction,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "address_internal_transactions_address_nt_t_idx",
    AddressInternalTransactions.address,
    desc(AddressInternalTransactions.block_timestamp),
    desc(AddressInternalTransactions.block_number),
    desc(AddressInternalTransactions.transaction_index),
)
