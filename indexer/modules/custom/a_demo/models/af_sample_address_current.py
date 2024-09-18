from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, TIMESTAMP

from common.models import HemeraModel, general_converter


class SampleAddressCurrent(HemeraModel):
    __tablename__ = "af_sample_address_current"

    address = Column(BYTEA, primary_key=True)
    transaction_count = Column(BIGINT)
    transfer_from_count = Column(BIGINT)
    transfer_from_value = Column(BIGINT)
    transfer_to_count = Column(BIGINT)
    transfer_to_value = Column(BIGINT)
    block_number = Column(BIGINT)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "SampleAddressCurrentD",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
