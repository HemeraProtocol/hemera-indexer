from sqlalchemy import Column, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, JSON, JSONB, SMALLINT, TIMESTAMP

from common.models import HemeraModel, general_converter


class AddressOpenseaTransactions(HemeraModel):
    __tablename__ = "af_opensea__transactions"

    address = Column(BYTEA, primary_key=True)
    is_offer = Column(BOOLEAN, primary_key=True)
    related_address = Column(BYTEA)
    transaction_type = Column(SMALLINT)

    order_hash = Column(BYTEA)
    zone = Column(BYTEA)

    offer = Column(JSONB)
    consideration = Column(JSONB)
    fee = Column(JSONB)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    transaction_hash = Column(BYTEA)
    block_number = Column(BIGINT, primary_key=True)
    log_index = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP)
    block_hash = Column(BYTEA, primary_key=True)
    reorg = Column(BOOLEAN, default=False)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "AddressOpenseaTransaction",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
