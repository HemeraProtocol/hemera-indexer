from datetime import datetime
from typing import Optional

from sqlalchemy import Column, desc, func, text
from sqlalchemy.dialects.postgresql import BOOLEAN, BYTEA, TIMESTAMP
from sqlmodel import Field, Index

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.log import Log


class Logs(HemeraModel, table=True):
    __tablename__ = "logs"

    # Primary keys
    log_index: int = Field(primary_key=True)
    transaction_hash: bytes = Field(primary_key=True)
    block_hash: bytes = Field(primary_key=True)

    # Log data
    address: Optional[bytes] = Field(default=None)
    data: Optional[bytes] = Field(default=None)
    topic0: Optional[bytes] = Field(default=None)
    topic1: Optional[bytes] = Field(default=None)
    topic2: Optional[bytes] = Field(default=None)
    topic3: Optional[bytes] = Field(default=None)

    # Block info
    transaction_index: Optional[int] = Field(default=None)
    block_number: Optional[int] = Field(default=None)
    block_timestamp: Optional[datetime] = Field(default=None)

    # Metadata
    create_time: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    update_time: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    reorg: bool = Field(default=False, sa_column=Column(BOOLEAN, server_default=text("false")))

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

    __table_args__ = (
        # Block timestamp index
        Index("logs_block_timestamp_index", desc("block_timestamp")),
        # Address with block number index
        Index(
            "logs_address_block_number_log_index_index",
            "address",
            desc("block_number"),
            desc("log_index"),
        ),
        # Block number with log index
        Index("logs_block_number_log_index_index", desc("block_number"), desc("log_index")),
        # Address with topic index
        Index(
            "logs_address_topic_0_number_log_index_index",
            "address",
            "topic0",
            desc("block_number"),
            desc("log_index"),
        ),
    )
