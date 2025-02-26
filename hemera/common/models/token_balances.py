from datetime import datetime
from decimal import Decimal
from typing import Optional, Type

from sqlalchemy import Column, desc, func, text
from sqlalchemy.dialects.postgresql import BOOLEAN, TIMESTAMP
from sqlmodel import Field, Index

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.token_balance import TokenBalance


def token_balances_general_converter(table: Type[HemeraModel], data: TokenBalance, is_update=False):
    if data.token_id is None:
        data.token_id = 0
    return general_converter(table, data, is_update)


class AddressTokenBalances(HemeraModel, table=True):
    __tablename__ = "address_token_balances"

    # Primary keys
    address: bytes = Field(primary_key=True)
    token_id: Decimal = Field(primary_key=True, max_digits=78)
    token_address: bytes = Field(primary_key=True)
    block_number: int = Field(primary_key=True)

    # Token info
    token_type: Optional[str] = Field(default=None)
    balance: Optional[Decimal] = Field(default=None, max_digits=100)

    # Block info
    block_timestamp: Optional[datetime] = Field(default=None)

    # Metadata
    create_time: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    update_time: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    reorg: bool = Field(default=False, sa_column=Column(BOOLEAN, server_default=text("false")))

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

    __table_args__ = (
        Index(
            "token_balance_address_id_number_index",
            "address",
            "token_address",
            desc("token_id"),
            desc("block_number"),
        ),
    )
