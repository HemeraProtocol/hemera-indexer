from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR
from sqlalchemy.sql import text

from common.models import HemeraModel, general_converter


class AddressTokenBalances(HemeraModel):
    __tablename__ = "address_token_balances"

    address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(78), primary_key=True)
    token_type = Column(VARCHAR)
    token_address = Column(BYTEA, primary_key=True)
    balance = Column(NUMERIC(100))

    block_number = Column(BIGINT, primary_key=True)
    block_timestamp = Column(TIMESTAMP)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, default=False)

    __table_args__ = (PrimaryKeyConstraint("address", "token_address", "token_id", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "TokenBalance",
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]


Index(
    "token_balance_address_id_number_index",
    AddressTokenBalances.address,
    AddressTokenBalances.token_address,
    desc(AddressTokenBalances.token_id),
    desc(AddressTokenBalances.block_number),
)
