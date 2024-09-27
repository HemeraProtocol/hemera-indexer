from sqlalchemy import Column, Index, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, JSON, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class OpenseaOrders(HemeraModel):
    __tablename__ = "af_opensea_na_orders"

    order_hash = Column(BYTEA)
    zone = Column(BYTEA)
    offerer = Column(BYTEA)
    recipient = Column(BYTEA)

    offer = Column(JSON)
    consideration = Column(JSON)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    transaction_hash = Column(BYTEA)
    block_number = Column(BIGINT, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    block_timestamp = Column(TIMESTAMP)
    block_hash = Column(BYTEA, primary_key=True)
    reorg = Column(BOOLEAN, server_default=text("false"))
    protocol_version = Column(VARCHAR, server_default="1.6")

    __table_args__ = (PrimaryKeyConstraint("block_number", "log_index", "block_hash"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "OpenseaOrder",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index("idx_order_hash", OpenseaOrders.order_hash)
