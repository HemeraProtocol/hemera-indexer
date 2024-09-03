from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from common.models import HemeraModel, general_converter


class AFTokenDepositsCurrent(HemeraModel):
    __tablename__ = "af_token_deposits_current"
    wallet_address = Column(BYTEA, primary_key=True)
    chain = Column(VARCHAR, primary_key=True)
    contract_address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    value = Column(NUMERIC(100))

    block_number = Column(BIGINT)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("wallet_address", "token_address", "contract_address", "chain"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "AddressTokenDeposit",
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_token_deposits_current.block_number",
                "converter": general_converter,
            }
        ]
