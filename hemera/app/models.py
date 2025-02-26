import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, EmailStr
from sqlmodel import Field, Relationship, SQLModel

"""
# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)

class TokenPayload(SQLModel):
    sub: str | None = None
"""


class PoolStatus(BaseModel):
    checkedin: int
    checkedout: int
    overflow: int
    size: int


class HealthCheckResponse(BaseModel):
    latest_block_number: int
    latest_block_timestamp: datetime
    engine_pool_status: str
    read_pool_status: str
    write_pool_status: str
    common_pool_status: str
    status: str = "OK"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ExplorerStats(BaseModel):
    total_transactions: int = Field(description="Total number of transactions")
    transaction_tps: float = Field(description="Transactions per second in last 10 minutes")
    latest_batch: int = Field(description="Latest batch number")
    latest_block: int = Field(description="Latest block number")
    avg_block_time: float = Field(description="Average block time")
    eth_price: str = Field(description="ETH price in USD")
    eth_price_btc: str = Field(description="ETH price in BTC")
    eth_price_diff: str = Field(description="ETH price difference percentage")
    native_token_price: str = Field(description="Native token price in USD")
    native_token_price_eth: str = Field(description="Native token price in ETH")
    native_token_price_diff: str = Field(description="Native token price difference percentage")
    dashboard_token_price_eth: str = Field(description="Dashboard token price in ETH")
    dashboard_token_price: str = Field(description="Dashboard token price in USD")
    dashboard_token_price_diff: str = Field(description="Dashboard token price difference percentage")
    gas_fee: str = Field(description="Current gas fee in Gwei")


class TransactionDay(BaseModel):
    value: str  # ISO format date
    count: int


class TransactionsDayResponse(BaseModel):
    title: str
    data: List[TransactionDay]


class SearchResultBase(BaseModel):
    type: str


class BlockSearchResult(SearchResultBase):
    type: str = "block"
    block_hash: str
    block_number: int


class AddressSearchResult(SearchResultBase):
    type: str = "address"
    wallet_address: str


class TransactionSearchResult(SearchResultBase):
    type: str = "transaction"
    transaction_hash: str


class TokenSearchResult(SearchResultBase):
    type: str = "token"
    token_name: str
    token_symbol: str
    token_address: str
    token_logo_url: Optional[str]


SearchResult = Union[BlockSearchResult, AddressSearchResult, TransactionSearchResult, TokenSearchResult]


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"
