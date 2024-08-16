from datetime import datetime

from sqlalchemy import INT, NUMERIC, SMALLINT, TEXT, Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, TIMESTAMP

from common.models import HemeraModel, general_converter


class AddressNftTransfers(HemeraModel):
    __tablename__ = "address_nft_transfers"

    address = Column(BYTEA, primary_key=True)
    block_number = Column(INT, primary_key=True)
    log_index = Column(INT, primary_key=True)
    transaction_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)
    block_hash = Column(BYTEA)
    token_address = Column(TEXT)
    the_other_address = Column(BYTEA)
    transfer_type = Column(SMALLINT)
    token_id = Column(NUMERIC(100))
    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())

    __table_args__ = (PrimaryKeyConstraint("address", "block_timestamp", "block_number", "log_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "AddressNftTransfer",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
