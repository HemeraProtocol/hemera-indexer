#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import Column, Index, PrimaryKeyConstraint, func, text
from sqlalchemy.dialects.postgresql import BIGINT, BOOLEAN, BYTEA, INTEGER, NUMERIC, TIMESTAMP

from common.models import HemeraModel, general_converter


class ERC721TokenMint(HemeraModel):
    __tablename__ = "erc721_token_mint"

    address = Column(BYTEA)
    token_address = Column(BYTEA, primary_key=True)
    token_id = Column(NUMERIC(100), primary_key=True)

    block_number = Column(BIGINT)
    block_timestamp = Column(TIMESTAMP)
    transaction_hash = Column(BYTEA)
    log_index = Column(INTEGER)

    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now())
    reorg = Column(BOOLEAN, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("token_address", "token_id"),)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": "ERC721TokenMint",
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            },
        ]


Index(
    "erc721_token_mint_address_id_index",
    ERC721TokenMint.token_address,
    ERC721TokenMint.token_id,
)
