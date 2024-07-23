from datetime import datetime

from sqlalchemy import Column, Index, desc, func
from sqlalchemy.dialects.postgresql import BYTEA, BIGINT, TIMESTAMP, NUMERIC, BOOLEAN

from common.models import HemeraModel
from indexer.domain.block import Block


class Blocks(HemeraModel):
    __tablename__ = 'blocks'
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
    internal_transactions_count = Column(BIGINT)

    state_root = Column(BYTEA)
    receipts_root = Column(BYTEA)
    withdrawals_root = Column(BYTEA)
    extra_data = Column(BYTEA)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)

    def model_domain_mapping(self):
        return [{
            'domain': 'Block',
            'update_strategy': None,
            'converter': self.converter,
        }]

    def converter(self, data: Block, is_update=False):
        converted_data = super().converter(data, is_update)
        converted_data['transactions_count'] = len(data.transactions) if data.transactions else 0



Index('blocks_timestamp_index', desc(Blocks.timestamp))
Index('blocks_number_index', desc(Blocks.number))

# +2yueshu
