from datetime import datetime
from sqlalchemy import Column, Index, PrimaryKeyConstraint, func, desc
from sqlalchemy.dialects.postgresql import BYTEA, BIGINT, TIMESTAMP, NUMERIC, BOOLEAN, VARCHAR

from common.models import HemeraModel


class AddressTokenBalances(HemeraModel):
    __tablename__ = 'address_token_balances'

    address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(78))
    token_type = Column(VARCHAR)
    token_address = Column(BYTEA, primary_key=True)
    balance = Column(NUMERIC(100))

    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (
        PrimaryKeyConstraint('address', 'token_address', 'block_number'),
    )


Index('token_balance_address_id_number_index',
      AddressTokenBalances.address, AddressTokenBalances.token_address,
      desc(AddressTokenBalances.token_id),
      desc(AddressTokenBalances.block_number))
