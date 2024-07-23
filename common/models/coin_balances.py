from datetime import datetime
from sqlalchemy import Column, Index, PrimaryKeyConstraint, func, desc
from sqlalchemy.dialects.postgresql import BYTEA, BIGINT, TIMESTAMP, NUMERIC, BOOLEAN

from common.models import HemeraModel


class CoinBalances(HemeraModel):
    __tablename__ = 'address_coin_balances'

    address = Column(BYTEA, primary_key=True)
    balance = Column(NUMERIC(100))
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (
        PrimaryKeyConstraint('address', 'block_number'),
    )


Index('coin_balance_address_number_desc_index',
      desc(CoinBalances.address), desc(CoinBalances.block_number))
