from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Index, PrimaryKeyConstraint, desc, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, NUMERIC, TIMESTAMP, VARCHAR
from sqlalchemy.sql import text
from sqlmodel import Field, Index

from hemera.common.models import HemeraModel
from hemera.common.models.token_balances import token_balances_general_converter
from hemera.indexer.domains.current_token_balance import CurrentTokenBalance


class CurrentTokenBalances(HemeraModel, table=True):
    __tablename__ = "address_current_token_balances"

    # Primary key fields
    address: bytes = Field(primary_key=True)
    token_id: Decimal = Field(primary_key=True, max_digits=78)
    token_address: bytes = Field(primary_key=True)

    # Token fields
    token_type: Optional[str] = Field(default=None)
    balance: Optional[Decimal] = Field(default=None, max_digits=100)

    # Block related fields
    block_number: Optional[int] = Field(default=None)
    block_timestamp: Optional[datetime] = Field(default=None)

    # Metadata fields
    create_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    update_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    reorg: Optional[bool] = Field(default=False)

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

    __table_args__ = (
        Index("current_token_balances_token_address_balance_of_index", text("token_address"), text("balance DESC")),
        Index(
            "current_token_balances_token_address_id_balance_of_index",
            text("token_address"),
            text("token_id"),
            text("balance DESC"),
        ),
    )
