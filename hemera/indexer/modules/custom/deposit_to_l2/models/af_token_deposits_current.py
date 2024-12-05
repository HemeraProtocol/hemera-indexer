from sqlalchemy import Column, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, NUMERIC, TIMESTAMP

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.modules.custom.deposit_to_l2.domain.address_token_deposit import AddressTokenDeposit


class AFTokenDepositsCurrent(HemeraModel):
    __tablename__ = "af_token_deposits_current"
    wallet_address = Column(BYTEA, primary_key=True)
    chain_id = Column(BIGINT, primary_key=True)
    contract_address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    value = Column(NUMERIC(100))

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (PrimaryKeyConstraint("wallet_address", "token_address", "contract_address", "chain_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AddressTokenDeposit,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number > af_token_deposits_current.block_number",
                "converter": general_converter,
            }
        ]
