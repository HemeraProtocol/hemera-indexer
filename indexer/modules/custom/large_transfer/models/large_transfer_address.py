from sqlalchemy import Column, func, PrimaryKeyConstraint, Computed
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, INTEGER, TIMESTAMP

from common.models import HemeraModel, general_converter


class LargeTransferAddress(HemeraModel):
    __tablename__ = "large_transfer_address"

    address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)

    transaction_count = Column(INTEGER, default=0, server_default='0')
    amount_in = Column(BIGINT)
    amount_out = Column(BIGINT)
    balance = Column(BIGINT, Computed("amount_in - amount_out"))
    block_number = Column(INTEGER)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("address", "token_address", name="large_transfer_address_token_address"),)


    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "LargeTransferAddressD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
