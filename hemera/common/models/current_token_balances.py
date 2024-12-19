from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel
from hemera.common.models.token_balances import token_balances_general_converter
from hemera.indexer.domains.current_token_balance import CurrentTokenBalance


class CurrentTokenBalances(HemeraModel):
    __tablename__ = "address_current_token_balances"

    address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(78), primary_key=True)
    token_type = Column(VARCHAR)
    token_address = Column(BYTEA, primary_key=True)
    balance = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("address", "token_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": CurrentTokenBalance,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > address_current_token_balances.block_number",
                "converter": token_balances_general_converter,
            }
        ]


Index(
    "current_token_balances_token_address_balance_of_index",
    CurrentTokenBalances.token_address,
    desc(CurrentTokenBalances.balance),
)
Index(
    "current_token_balances_token_address_id_balance_of_index",
    CurrentTokenBalances.token_address,
    CurrentTokenBalances.token_id,
    desc(CurrentTokenBalances.balance),
)
