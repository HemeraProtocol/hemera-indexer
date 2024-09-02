from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class AFTokenDepositsTransactions(HemeraModel):
    __tablename__ = "af_token_deposits__transactions"
    transaction_hash = Column(BYTEA, primary_key=True)
    wallet_address = Column(BYTEA)
    chain = Column(VARCHAR)
    contract_address = Column(BYTEA)
    token_address = Column(BYTEA)
    value = Column(NUMERIC(100))

    block_number = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "TokenDepositTransaction",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
