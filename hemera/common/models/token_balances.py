from typing import Type

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.token_balance import TokenBalance


def token_balances_general_converter(table: Type[HemeraModel], data: TokenBalance, is_update=False):

    if data.token_id is None:
        data.token_id = -1

    return general_converter(table, data, is_update)


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
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("address", "token_address", "token_id", "block_number"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": TokenBalance,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": token_balances_general_converter,
            }
        ]


Index(
    "token_balance_address_id_number_index",
    AddressTokenBalances.address,
    AddressTokenBalances.token_address,
    desc(AddressTokenBalances.token_id),
    desc(AddressTokenBalances.block_number),
)
