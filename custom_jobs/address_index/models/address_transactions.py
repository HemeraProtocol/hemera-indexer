from sqlalchemy import Column, Index, desc, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, NUMERIC, SMALLINT, TEXT, TIMESTAMP

from common.models import HemeraModel, general_converter
from custom_jobs.address_index.domain import AddressTransaction


class AddressTransactions(HemeraModel):
    __tablename__ = "address_transactions"

    address = Column(BYTEA, primary_key=True)
    block_number = Column(INTEGER, primary_key=True)
    transaction_index = Column(INTEGER, primary_key=True)
    transaction_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP, primary_key=True)
    block_hash = Column(BYTEA)
    txn_type = Column(SMALLINT)
    related_address = Column(BYTEA)
    value = Column(NUMERIC(100))
    transaction_fee = Column(NUMERIC(100))
    receipt_status = Column(INTEGER)
    method = Column(TEXT)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AddressTransaction,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "address_transactions_address_block_timestamp_block_number_t_idx",
    AddressTransactions.address,
    desc(AddressTransactions.block_timestamp),
    desc(AddressTransactions.block_number),
    desc(AddressTransactions.transaction_index),
)

Index(
    "address_transactions_address_txn_type_block_timestamp_block_idx",
    AddressTransactions.address,
    AddressTransactions.txn_type,
    desc(AddressTransactions.block_timestamp),
    desc(AddressTransactions.block_number),
    desc(AddressTransactions.transaction_index),
)
