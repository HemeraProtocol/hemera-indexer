from datetime import datetime

from sqlalchemy import INT, NUMERIC, SMALLINT, Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, TIMESTAMP

from common.models import HemeraModel, general_converter


class AddressTransactions(HemeraModel):
    __tablename__ = "address_transactions"

    address = Column(BYTEA, primary_key=True)
    block_number = Column(INT, primary_key=True)
    transaction_index = Column(INT, primary_key=True)
    transaction_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)
    block_hash = Column(BYTEA)
    txn_type = Column(SMALLINT)
    the_other_address = Column(BYTEA)
    value = Column(NUMERIC(100))
    transaction_fee = Column(NUMERIC(100))
    receipt_status = Column(INT)
    method = Column(BYTEA)
    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("address", "block_timestamp", "block_number", "transaction_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "AddressTransaction",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
