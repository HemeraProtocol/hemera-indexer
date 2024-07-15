from sqlalchemy import Column, INTEGER
from sqlalchemy.dialects.postgresql import BYTEA, BIGINT, TIMESTAMP

from exporters.jdbc.schema import Base


class OpBedrockStateBatches(Base):
    __tablename__ = 'op_bedrock_state_batches'

    batch_index = Column(BIGINT, primary_key=True)
    l1_block_number = Column(BIGINT)
    l1_block_timestamp = Column(TIMESTAMP)
    l1_block_hash = Column(BYTEA)
    l1_transaction_hash = Column(BYTEA)
    batch_root = Column(BYTEA)
    start_block_number = Column(BIGINT)
    end_block_number = Column(BIGINT)
    transaction_count = Column(INTEGER)
    block_count = Column(INTEGER)
