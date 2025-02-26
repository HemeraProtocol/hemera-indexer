from datetime import datetime
from decimal import Decimal
from typing import Optional, Type
from urllib import parse

from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import BIGINT, BYTEA, JSONB, NUMERIC, TIMESTAMP, VARCHAR
from sqlmodel import Field, Index

from hemera.common.models import HemeraModel, general_converter
from hemera.indexer.domains.token_id_infos import (
    ERC721TokenIdChange,
    ERC721TokenIdDetail,
    ERC1155TokenIdDetail,
    UpdateERC721TokenIdDetail,
    UpdateERC1155TokenIdDetail,
)


def token_uri_format_converter(table: Type[HemeraModel], data, is_update=False):
    if data.token_uri is not None:
        data.token_uri = parse.quote_plus(data.token_uri)
    return general_converter(table, data, is_update)


class ERC1155TokenIdDetails(HemeraModel, table=True):
    __tablename__ = "erc1155_token_id_details"

    token_address: bytes = Field(sa_column=Column(BYTEA, primary_key=True))
    token_id: Decimal = Field(sa_column=Column(NUMERIC(100), primary_key=True))
    token_supply: Optional[Decimal] = Field(sa_column=Column(NUMERIC(78)))
    token_uri: Optional[str] = Field(sa_column=Column(VARCHAR))
    token_uri_info: Optional[dict] = Field(sa_column=Column(JSONB))

    block_number: Optional[int] = Field(sa_column=Column(BIGINT))
    block_timestamp: Optional[datetime] = Field(sa_column=Column(TIMESTAMP))

    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)
    reorg: bool = Field(default=False)

    __table_args__ = (Index("erc1155_detail_desc_address_id_index", text("token_address DESC, token_id")),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": ERC1155TokenIdDetail,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": token_uri_format_converter,
            },
            {
                "domain": UpdateERC1155TokenIdDetail,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number >= erc1155_token_id_details.block_number",
                "converter": general_converter,
            },
        ]


class ERC721TokenIdDetails(HemeraModel, table=True):
    __tablename__ = "erc721_token_id_details"

    token_address: bytes = Field(sa_column=Column(BYTEA, primary_key=True))
    token_id: Decimal = Field(sa_column=Column(NUMERIC(100), primary_key=True))
    token_owner: Optional[bytes] = Field(sa_column=Column(BYTEA))
    token_uri: Optional[str] = Field(sa_column=Column(VARCHAR))
    token_uri_info: Optional[dict] = Field(sa_column=Column(JSONB))

    block_number: Optional[int] = Field(sa_column=Column(BIGINT))
    block_timestamp: Optional[datetime] = Field(sa_column=Column(TIMESTAMP))

    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)
    reorg: bool = Field(default=False)

    __table_args__ = (Index("erc721_detail_owner_address_id_index", text("token_owner DESC, token_address, token_id")),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": ERC721TokenIdDetail,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": token_uri_format_converter,
            },
            {
                "domain": UpdateERC721TokenIdDetail,
                "conflict_do_update": True,
                "update_strategy": "EXCLUDED.block_number >= erc721_token_id_details.block_number",
                "converter": general_converter,
            },
        ]


class ERC721TokenIdChanges(HemeraModel, table=True):
    __tablename__ = "erc721_token_id_changes"

    token_address: bytes = Field(sa_column=Column(BYTEA, primary_key=True))
    token_id: Decimal = Field(sa_column=Column(NUMERIC(100), primary_key=True))
    token_owner: Optional[bytes] = Field(sa_column=Column(BYTEA))

    block_number: int = Field(sa_column=Column(BIGINT, primary_key=True))
    block_timestamp: Optional[datetime] = Field(sa_column=Column(TIMESTAMP))

    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)
    reorg: bool = Field(default=False)

    __table_args__ = (
        Index("erc721_change_address_id_number_desc_index", text("token_address, token_id, block_number DESC")),
    )

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": ERC721TokenIdChange,
                "conflict_do_update": False,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]
