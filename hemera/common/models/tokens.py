from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

from sqlalchemy import Column, desc, func, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlmodel import Field, Index

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.token import MarkBalanceToken, MarkTotalSupplyToken, Token, UpdateToken


class Tokens(HemeraModel, table=True):
    __tablename__ = "tokens"

    # Primary key
    address: bytes = Field(primary_key=True)

    # Token basic info
    token_type: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    symbol: Optional[str] = Field(default=None)
    decimals: Optional[Decimal] = Field(default=None, max_digits=100)
    total_supply: Optional[Decimal] = Field(default=None, max_digits=100)
    block_number: Optional[int] = Field(default=None)

    # Token statistics
    holder_count: Optional[int] = Field(default=0)
    transfer_count: Optional[int] = Field(default=0)
    icon_url: Optional[str] = Field(default=None)
    urls: Optional[Dict] = Field(default=None, sa_column=Column(JSONB))
    volume_24h: Optional[Decimal] = Field(default=None, max_digits=38, decimal_places=2)
    price: Optional[Decimal] = Field(default=None, max_digits=38, decimal_places=6)
    previous_price: Optional[Decimal] = Field(default=None, max_digits=38, decimal_places=6)
    market_cap: Optional[Decimal] = Field(default=None, max_digits=38, decimal_places=2)
    on_chain_market_cap: Optional[Decimal] = Field(default=None, max_digits=38, decimal_places=2)
    is_verified: bool = Field(default=False)

    # External IDs
    cmc_id: Optional[int] = Field(default=None)
    cmc_slug: Optional[str] = Field(default=None)
    gecko_id: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    no_balance_of: bool = Field(default=False)
    fail_balance_of_count: Optional[int] = Field(default=0)
    succeed_balance_of_count: Optional[int] = Field(default=0)
    no_total_supply: bool = Field(default=False)
    fail_total_supply_count: Optional[int] = Field(default=0)

    # Metadata
    create_time: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    update_time: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP, server_default=func.now())
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": Token,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            },
            {
                "domain": UpdateToken,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number >= tokens.block_number",
                "converter": general_converter,
            },
            {
                "domain": MarkTotalSupplyToken,
                "conflict_do_update": True,
                "update_strategy": None,
                # "update_strategy": "EXCLUDED.block_number >= tokens.block_number",
                "converter": general_converter,
            },
            {
                "domain": MarkBalanceToken,
                "conflict_do_update": True,
                "update_strategy": None,
                # "update_strategy": "EXCLUDED.block_number >= tokens.block_number",
                "converter": general_converter,
            },
        ]

    __table_args__ = (
        Index("tokens_name_index", "name"),
        Index("tokens_symbol_index", "symbol"),
        Index("tokens_type_index", "token_type"),
        Index("tokens_type_holders_index", "token_type", desc("holder_count")),
        Index("tokens_type_on_chain_market_cap_index", "token_type", desc("on_chain_market_cap")),
        # Note: tsvector index needs to be created manually
        # CREATE INDEX tokens_tsvector_symbol_name_index
        # ON tokens
        # USING gin (to_tsvector('english', (symbol || ' ' || name)));
    )
