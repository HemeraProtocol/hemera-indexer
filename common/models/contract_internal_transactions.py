from datetime import datetime

from sqlalchemy import Column, Index, desc, func
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TEXT, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class ContractInternalTransactions(HemeraModel):
    __tablename__ = "contract_internal_transactions"

    trace_id = Column(VARCHAR, primary_key=True)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    value = Column(NUMERIC(100))
    trace_type = Column(VARCHAR)
    call_type = Column(VARCHAR)
    gas = Column(NUMERIC(100))
    gas_used = Column(NUMERIC(100))
    trace_address = Column(ARRAY(INTEGER))
    error = Column(TEXT)
    status = Column(INTEGER)
    block_number = Column(BIGINT)
    block_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)
    transaction_index = Column(INTEGER)
    transaction_hash = Column(BYTEA)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ContractInternalTransaction",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "contract_internal_transactions_transaction_hash_idx",
    ContractInternalTransactions.transaction_hash,
)
Index(
    "internal_transactions_block_number_index",
    desc(ContractInternalTransactions.block_number),
)
Index(
    "internal_transactions_number_transaction_index",
    desc(ContractInternalTransactions.block_number),
    desc(ContractInternalTransactions.transaction_index),
)
Index(
    "internal_transactions_from_address_number_transaction_index",
    ContractInternalTransactions.from_address,
    desc(ContractInternalTransactions.block_number),
    desc(ContractInternalTransactions.transaction_index),
)
Index(
    "internal_transactions_to_address_number_transaction_index",
    ContractInternalTransactions.to_address,
    desc(ContractInternalTransactions.block_number),
    desc(ContractInternalTransactions.transaction_index),
)
