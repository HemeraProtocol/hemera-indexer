from datetime import datetime
from sqlalchemy import Column, Index, desc, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, BIGINT, TIMESTAMP, NUMERIC,  BOOLEAN
from exporters.jdbc.schema import Base


class ERC1155TokenTransfers(Base):
    __tablename__ = 'erc1155_token_transfers'

    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    token_address = Column(BYTEA)
    token_id = Column(NUMERIC(78))
    value = Column(NUMERIC)

    block_number = Column(BIGINT)
    block_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    relog = Column(BOOLEAN, default=False)

    __table_args__ = (
        PrimaryKeyConstraint('transaction_hash', 'log_index'),
    )


Index('erc1155_token_transfers_block_timestamp_index', desc(ERC1155TokenTransfers.block_timestamp))

Index('erc1155_token_transfers_address_block_number_log_index_index',
      ERC1155TokenTransfers.token_address, ERC1155TokenTransfers.from_address, ERC1155TokenTransfers.to_address,
      desc(ERC1155TokenTransfers.block_number), desc(ERC1155TokenTransfers.log_index))
