from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Field, Index

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.coin_balance import CoinBalance


class CoinBalances(HemeraModel, table=True):
    __tablename__ = "address_coin_balances"

    # Primary key fields
    address: bytes = Field(primary_key=True)
    block_number: int = Field(primary_key=True)

    # Balance and timestamp fields
    balance: Optional[Decimal] = Field(default=None, max_digits=100)
    block_timestamp: Optional[datetime] = Field(default=None)

    # Metadata fields
    create_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    update_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    reorg: Optional[bool] = Field(default=False)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": CoinBalance,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]

    __table_args__ = (Index("coin_balance_address_number_desc_index", text("address DESC"), text("block_number DESC")),)
