from datetime import datetime
from sqlalchemy import Column, Index, desc, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BYTEA, INTEGER, BIGINT, TIMESTAMP, NUMERIC, BOOLEAN

from common.models import db


class ERC20TokenTransfers(db.Model):
    __tablename__ = 'erc20_token_transfers'

    transaction_hash = Column(BYTEA, primary_key=True)
    log_index = Column(INTEGER, primary_key=True)
    from_address = Column(BYTEA)
    to_address = Column(BYTEA)
    token_address = Column(BYTEA)
    value = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_hash = Column(BYTEA)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (
        PrimaryKeyConstraint('transaction_hash', 'log_index'),
    )


Index('erc20_token_transfers_block_timestamp_index', desc(ERC20TokenTransfers.block_timestamp))
Index('erc20_token_transfers_number_log_index',
      desc(ERC20TokenTransfers.block_number),
      desc(ERC20TokenTransfers.log_index))

Index('erc20_token_transfers_from_address_number_log_index_index',
      ERC20TokenTransfers.from_address, desc(ERC20TokenTransfers.block_number), desc(ERC20TokenTransfers.log_index))
Index('erc20_token_transfers_to_address_number_log_index_index',
      ERC20TokenTransfers.to_address, desc(ERC20TokenTransfers.block_number), desc(ERC20TokenTransfers.log_index))
Index('erc20_token_transfers_token_address_number_log_index_index',
      ERC20TokenTransfers.token_address, desc(ERC20TokenTransfers.block_number), desc(ERC20TokenTransfers.log_index))
