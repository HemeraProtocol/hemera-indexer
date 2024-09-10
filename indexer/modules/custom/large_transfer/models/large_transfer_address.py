from sqlalchemy import Column, Computed, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TEXT, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class LargeTransferAddress(HemeraModel):
    __tablename__ = "large_transfer_address"

    address = Column(BYTEA, primary_key=True)

    transaction_count = Column(INTEGER)
    amount = Column(NUMERIC(100))
    block_number = Column(INTEGER)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

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