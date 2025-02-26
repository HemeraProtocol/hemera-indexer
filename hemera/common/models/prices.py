from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.sql import text
from sqlmodel import Field, Index

from hemera.common.models import HemeraModel


class TokenPrices(HemeraModel, table=True):
    """Historical token prices model

    Primary keys:
    - symbol: Token symbol
    - timestamp: Price timestamp
    """

    __tablename__ = "token_prices"

    # Primary key fields
    symbol: str = Field(primary_key=True)
    timestamp: datetime = Field(primary_key=True)

    # Price field
    price: Optional[Decimal] = Field(default=None, description="Token price at the timestamp")

    __table_args__ = (
        Index("token_prices_symbol_timestamp_index", text("symbol ASC, timestamp DESC")),
        Index("token_prices_timestamp_index", text("timestamp DESC")),
    )


class TokenHourlyPrices(HemeraModel, table=True):
    """Historical hourly token prices model

    Primary keys:
    - symbol: Token symbol
    - timestamp: Price timestamp
    """

    __tablename__ = "token_hourly_prices"

    # Primary key fields
    symbol: str = Field(primary_key=True)
    timestamp: datetime = Field(primary_key=True)

    # Price field
    price: Optional[Decimal] = Field(default=None, description="Token price at the timestamp")

    __table_args__ = (
        Index("token_hourly_prices_symbol_timestamp_index", text("symbol ASC, timestamp DESC")),
        Index("token_hourly_prices_timestamp_index", text("timestamp DESC")),
    )


class CoinPrices(HemeraModel, table=True):
    """Daily coin prices model

    Primary key:
    - block_date: Price date from block
    """

    __tablename__ = "coin_prices"

    # Primary key field
    block_date: datetime = Field(primary_key=True, description="Block date for the price")

    # Price field
    price: Optional[Decimal] = Field(default=None, description="Coin price on the block date")

    __table_args__ = (Index("coin_prices_block_date_index", text("block_date DESC")),)
