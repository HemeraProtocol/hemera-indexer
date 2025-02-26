from datetime import datetime
from decimal import Decimal
from typing import Optional, Type, Union

from sqlalchemy.sql import text
from sqlmodel import Field, Index

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.block import Block, UpdateBlockInternalCount


class Blocks(HemeraModel, table=True):
    __tablename__ = "blocks"

    # Primary key and basic fields
    hash: bytes = Field(primary_key=True)
    number: Optional[int] = Field(default=None)
    timestamp: Optional[datetime] = Field(default=None)
    parent_hash: Optional[bytes] = Field(default=None)
    nonce: Optional[bytes] = Field(default=None)

    # Gas related fields
    gas_limit: Optional[Decimal] = Field(default=None, max_digits=100)
    gas_used: Optional[Decimal] = Field(default=None, max_digits=100)
    base_fee_per_gas: Optional[Decimal] = Field(default=None, max_digits=100)
    blob_gas_used: Optional[Decimal] = Field(default=None, max_digits=100)
    excess_blob_gas: Optional[Decimal] = Field(default=None, max_digits=100)

    # Blockchain specific fields
    difficulty: Optional[Decimal] = Field(default=None, max_digits=38)
    total_difficulty: Optional[Decimal] = Field(default=None, max_digits=38)
    size: Optional[int] = Field(default=None)
    miner: Optional[bytes] = Field(default=None)
    sha3_uncles: Optional[bytes] = Field(default=None)
    transactions_root: Optional[bytes] = Field(default=None)
    transactions_count: Optional[int] = Field(default=None)
    traces_count: Optional[int] = Field(default=0)
    internal_transactions_count: Optional[int] = Field(default=0)

    # Root fields
    state_root: Optional[bytes] = Field(default=None)
    receipts_root: Optional[bytes] = Field(default=None)
    withdrawals_root: Optional[bytes] = Field(default=None)
    extra_data: Optional[bytes] = Field(default=None)

    # Metadata fields
    create_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    update_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    reorg: Optional[bool] = Field(default=False)

    __query_order__ = [number]

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": Block,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": converter,
            },
            {
                "domain": UpdateBlockInternalCount,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": converter,
            },
        ]

    __table_args__ = (
        Index("blocks_timestamp_index", text("timestamp DESC")),
        Index("blocks_number_index", text("timestamp DESC")),
        Index("blocks_number_unique_when_not_reorg", "number", unique=True, postgresql_where="reorg = false"),
        Index("blocks_hash_unique_when_not_reorg", "hash", unique=True, postgresql_where="reorg = false"),
    )


def converter(
    table: Type[HemeraModel],
    data: Union[Block, UpdateBlockInternalCount],
    is_update=False,
):
    converted_data = general_converter(table, data, is_update)
    if isinstance(data, Block):
        converted_data["transactions_count"] = len(data.transactions) if data.transactions else 0

    return converted_data
