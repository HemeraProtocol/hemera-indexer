from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domain.log import Log


class Logs(HemeraModel):
    __tablename__ = "logs"

    log_index = Column(INTEGER, primary_key=True)
    address = Column(BYTEA)
    data = Column(BYTEA)
    topic0 = Column(BYTEA)
    topic1 = Column(BYTEA)
    topic2 = Column(BYTEA)
    topic3 = Column(BYTEA)
    transaction_hash = Column(BYTEA, primary_key=True)
    transaction_index = Column(INTEGER)
    block_number = Column(BIGINT)
    block_hash = Column(BYTEA, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("transaction_hash", "block_hash", "log_index"),)
    __query_order__ = [block_number, log_index]

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": Log,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index("logs_block_timestamp_index", desc(Logs.block_timestamp))
Index(
    "logs_address_block_number_log_index_index",
    Logs.address,
    desc(Logs.block_number),
    desc(Logs.log_index),
)
Index("logs_block_number_log_index_index", desc(Logs.block_number), desc(Logs.log_index))
Index(
    "logs_address_topic_0_number_log_index_index",
    Logs.address,
    Logs.topic0,
    desc(Logs.block_number),
    desc(Logs.log_index),
)
