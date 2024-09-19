from datetime import datetime

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class AfKarakRecords(HemeraModel):
    __tablename__ = "af_karak_records"
    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    block_number = Column(BIGINT)
    block_timestamp = Column(BIGINT)
    method = Column(VARCHAR)
    event_name = Column(VARCHAR)
    topic0 = Column(VARCHAR)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)

    vault = Column(BYTEA)
    amount = Column(NUMERIC(100))

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("transaction_hash", "log_index"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "UniswapV3SwapEvent",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": "AgniV3SwapEvent",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]
