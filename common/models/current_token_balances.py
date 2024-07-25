from datetime import datetime
from sqlalchemy import Column, Index, PrimaryKeyConstraint, func, desc
from sqlalchemy.dialects.postgresql import BYTEA, BIGINT, TIMESTAMP, NUMERIC, BOOLEAN, VARCHAR

from common.models import HemeraModel, general_converter


class CurrentTokenBalances(HemeraModel):
    __tablename__ = 'address_current_token_balances'

    address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), default=-1)
    token_type = Column(VARCHAR)
    token_address = Column(BYTEA, primary_key=True)
    balance = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, default=datetime.utcnow)
    update_time = Column(TIMESTAMP, onupdate=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (
        PrimaryKeyConstraint('address', 'token_address'),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                'domain': 'CurrentTokenBalance',
                'conflict_do_update': True,
                'update_strategy': "EXCLUDED.block_number > address_current_token_balances.block_number",
                'converter': general_converter,
            }
        ]


Index('current_token_balances_token_address_balance_of_index',
      CurrentTokenBalances.token_address, desc(CurrentTokenBalances.balance))
Index('current_token_balances_token_address_id_balance_of_index',
      CurrentTokenBalances.token_address, CurrentTokenBalances.token_id,
      desc(CurrentTokenBalances.balance))
