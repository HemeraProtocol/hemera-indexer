from sqlalchemy import Column, PrimaryKeyConstraint, func, text
from common.models import HemeraModel, general_converter
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR


class AddressTokenBalances(HemeraModel):
    __tablename__ = "lido_seth_share_balances"

    address = Column(BYTEA, primary_key=True)
    token_address = Column(BYTEA, primary_key=True)
    balance = Column(NUMERIC(100))
    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("address", "token_address"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "LidoShareBalance",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]

