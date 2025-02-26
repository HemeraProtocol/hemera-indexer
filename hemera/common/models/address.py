#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/23 16:35
# @Author  ideal93
# @File  address.py
# @Brief

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Computed, Index, Integer, text
from sqlmodel import Field

from hemera.common.models import HemeraModel, general_converter
from hemera_udf.address_index.domains import AddressInternalTransaction


class AddressInternalTransactions(HemeraModel, table=True):
    __tablename__ = "address_internal_transactions"

    # Primary key fields
    address: bytes = Field(primary_key=True)
    trace_id: str = Field(primary_key=True)
    block_number: int = Field(primary_key=True)
    transaction_index: int = Field(primary_key=True)
    block_timestamp: datetime = Field(primary_key=True)
    trace_type: Optional[str] = Field(default=None)

    # Additional fields
    related_address: Optional[bytes] = Field(default=None)
    transaction_receipt_status: Optional[int] = Field(default=None)

    # Transaction related fields
    transaction_hash: Optional[bytes] = Field(default=None)
    block_hash: Optional[bytes] = Field(default=None)
    error: Optional[str] = Field(default=None)
    status: Optional[int] = Field(default=None)
    input_method: Optional[str] = Field(default=None)

    # Numerical fields
    value: Optional[Decimal] = Field(default=None, max_digits=100)
    gas: Optional[Decimal] = Field(default=None, max_digits=100)
    gas_used: Optional[Decimal] = Field(default=None, max_digits=100)

    # Type fields
    call_type: Optional[str] = Field(default=None)
    txn_type: Optional[int] = Field(default=None)

    # Metadata fields
    create_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    update_time: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @staticmethod
    def model_domain_mapping():
        return [
            {
                "domain": AddressInternalTransaction,
                "conflict_do_update": True,
                "update_strategy": None,
                "converter": general_converter,
            }
        ]

    __table_args__ = (
        Index(
            "address_internal_transactions_address_idx",
            "address",
            text("block_timestamp DESC"),
            text("block_number DESC"),
            text("transaction_index DESC"),
        ),
    )


class AddressIndexStats(HemeraModel, table=True):
    __tablename__ = "af_index_stats"

    # Primary key and basic fields
    address: bytes = Field(primary_key=True)

    # Transaction count
    transaction_in_count: int = Field(default=0)
    transaction_out_count: int = Field(default=0)
    transaction_self_count: int = Field(default=0)

    transaction_in_value: Decimal = Field(default=0)
    transaction_out_value: Decimal = Field(default=0)
    transaction_self_value: Decimal = Field(default=0)

    transaction_in_fee: Decimal = Field(default=0)
    transaction_out_fee: Decimal = Field(default=0)
    transaction_self_fee: Decimal = Field(default=0)

    # Internal transaction count
    internal_transaction_in_count: int = Field(default=0)
    internal_transaction_out_count: int = Field(default=0)
    internal_transaction_self_count: int = Field(default=0)

    internal_transaction_in_value: Decimal = Field(default=0)
    internal_transaction_out_value: Decimal = Field(default=0)
    internal_transaction_self_value: Decimal = Field(default=0)

    # ERC20 transfer count
    erc20_transfer_in_count: int = Field(default=0)
    erc20_transfer_out_count: int = Field(default=0)
    erc20_transfer_self_count: int = Field(default=0)

    # NFT transfer count
    nft_transfer_in_count: int = Field(default=0)
    nft_transfer_out_count: int = Field(default=0)
    nft_transfer_self_count: int = Field(default=0)

    # NFT 721 transfer count
    nft_721_transfer_in_count: int = Field(default=0)
    nft_721_transfer_out_count: int = Field(default=0)
    nft_721_transfer_self_count: int = Field(default=0)

    # NFT 1155 transfer count
    nft_1155_transfer_in_count: int = Field(default=0)
    nft_1155_transfer_out_count: int = Field(default=0)
    nft_1155_transfer_self_count: int = Field(default=0)

    # Contract count
    contract_creation_count: int = Field(default=0)
    contract_destruction_count: int = Field(default=0)
    contract_operation_count: int = Field(default=0)

    # Total transaction count (generated column)
    transaction_count: int = Field(default=0)
    # Total internal transaction count (generated column)
    internal_transaction_count: int = Field(
        sa_column=Column(
            "internal_transaction_count",
            Integer,
            Computed(
                "internal_transaction_in_count + internal_transaction_out_count + internal_transaction_self_count"
            ),
        )
    )
    # Total ERC20 transfer count (generated column)
    erc20_transfer_count: int = Field(
        sa_column=Column(
            "erc20_transfer_count",
            Integer,
            Computed("erc20_transfer_in_count + erc20_transfer_out_count + erc20_transfer_self_count"),
        )
    )
    # Total NFT transfer count (generated column)
    nft_transfer_count: int = Field(
        sa_column=Column(
            "nft_transfer_count",
            Integer,
            Computed("nft_transfer_in_count + nft_transfer_out_count + nft_transfer_self_count"),
        )
    )
    # Total NFT 721 transfer count (generated column)
    nft_721_transfer_count: int = Field(
        sa_column=Column(
            "nft_721_transfer_count",
            Integer,
            Computed("nft_721_transfer_in_count + nft_721_transfer_out_count + nft_721_transfer_self_count"),
        )
    )

    # Total NFT 1155 transfer count (generated column)
    nft_1155_transfer_count: int = Field(
        sa_column=Column(
            "nft_1155_transfer_count",
            Integer,
            Computed("nft_1155_transfer_in_count + nft_1155_transfer_out_count + nft_1155_transfer_self_count"),
        )
    )

    tag: Optional[str] = Field(default=None)
