from datetime import datetime

from sqlalchemy import INT, SMALLINT, TEXT, Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class AddressTokenTransfers(HemeraModel):
    __tablename__ = "address_token_transfers"

    address = Column(BYTEA, primary_key=True)
    block_number = Column(INT, primary_key=True)
    log_index = Column(INT, primary_key=True)
    transaction_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP, primary_key=True)
    block_hash = Column(BYTEA)
    token_address = Column(BYTEA)
    the_other_address = Column(BYTEA)
    transfer_type = Column(SMALLINT)
    value = Column(NUMERIC(100))
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("address", "block_timestamp", "block_number", "log_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "AddressTokenTransfer",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
