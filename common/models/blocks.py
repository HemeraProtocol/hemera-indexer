from datetime import datetime
from typing import Type, Union

from sqlalchemy import Column, Index, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter
from indexer.domain.block import Block, UpdateBlockInternalCount


class Blocks(HemeraModel):
    __tablename__ = "blocks"
    hash = Column(BYTEA, primary_key=True)
    number = Column(BIGINT)
    timestamp = Column(TIMESTAMP)
    parent_hash = Column(BYTEA)
    nonce = Column(BYTEA)

    gas_limit = Column(NUMERIC(100))
    gas_used = Column(NUMERIC(100))
    base_fee_per_gas = Column(NUMERIC(100))
    blob_gas_used = Column(NUMERIC(100))
    excess_blob_gas = Column(NUMERIC(100))

    # for pow,pos
    difficulty = Column(NUMERIC(38))
    total_difficulty = Column(NUMERIC(38))
    size = Column(BIGINT)
    miner = Column(BYTEA)
    sha3_uncles = Column(BYTEA)
    transactions_root = Column(BYTEA)
    transactions_count = Column(BIGINT)
    traces_count = Column(BIGINT, default=0)
    internal_transactions_count = Column(BIGINT, default=0)

    state_root = Column(BYTEA)
    receipts_root = Column(BYTEA)
    withdrawals_root = Column(BYTEA)
    extra_data = Column(BYTEA)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "Block",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": converter,
            },
            {
                "domain": "UpdateBlockInternalCount",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": converter,
            },
        ]


Index("blocks_timestamp_index", desc(Blocks.timestamp))
Index("blocks_number_index", desc(Blocks.number))
Index(
    "blocks_number_unique_when_not_reorg",
    Blocks.number,
    unique=True,
    postgresql_where=(Blocks.reorg == False),
)
Index(
    "blocks_hash_unique_when_not_reorg",
    Blocks.hash,
    unique=True,
    postgresql_where=(Blocks.reorg == False),
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
