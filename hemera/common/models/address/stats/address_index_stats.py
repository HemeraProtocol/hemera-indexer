#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2025/2/18 18:07
# @Author  ideal93
# @File  address_index_stats.py
# @Brief
from decimal import Decimal
from typing import Optional

from sqlmodel import Field

from hemera.common.models import HemeraModel


class AddressIndexStats(HemeraModel, table=True):
    __tablename__ = "af_index_stats"

    address: bytes = Field(primary_key=True)

    transaction_in_count: Optional[int] = Field(default=None)
    transaction_out_count: Optional[int] = Field(default=None)
    transaction_self_count: Optional[int] = Field(default=None)

    transaction_in_value: Optional[Decimal] = Field(default=None)
    transaction_out_value: Optional[Decimal] = Field(default=None)
    transaction_self_value: Optional[Decimal] = Field(default=None)

    transaction_in_fee: Optional[Decimal] = Field(default=None)
    transaction_out_fee: Optional[Decimal] = Field(default=None)
    transaction_self_fee: Optional[Decimal] = Field(default=None)

    internal_transaction_in_count: Optional[int] = Field(default=None)
    internal_transaction_out_count: Optional[int] = Field(default=None)
    internal_transaction_self_count: Optional[int] = Field(default=None)

    internal_transaction_in_value: Optional[Decimal] = Field(default=None)
    internal_transaction_out_value: Optional[Decimal] = Field(default=None)
    internal_transaction_self_value: Optional[Decimal] = Field(default=None)

    erc20_transfer_in_count: Optional[int] = Field(default=None)
    erc20_transfer_out_count: Optional[int] = Field(default=None)
    erc20_transfer_self_count: Optional[int] = Field(default=None)

    nft_transfer_in_count: Optional[int] = Field(default=None)
    nft_transfer_out_count: Optional[int] = Field(default=None)
    nft_transfer_self_count: Optional[int] = Field(default=None)

    nft_721_transfer_in_count: Optional[int] = Field(default=None)
    nft_721_transfer_out_count: Optional[int] = Field(default=None)
    nft_721_transfer_self_count: Optional[int] = Field(default=None)

    nft_1155_transfer_in_count: Optional[int] = Field(default=None)
    nft_1155_transfer_out_count: Optional[int] = Field(default=None)
    nft_1155_transfer_self_count: Optional[int] = Field(default=None)

    contract_creation_count: Optional[int] = Field(default=None)
    contract_destruction_count: Optional[int] = Field(default=None)
    contract_operation_count: Optional[int] = Field(default=None)

    transaction_count: Optional[int] = Field(default=None)
    internal_transaction_count: Optional[int] = Field(default=None)
    erc20_transfer_count: Optional[int] = Field(default=None)

    nft_transfer_count: Optional[int] = Field(default=None)
    nft_721_transfer_count: Optional[int] = Field(default=None)
    nft_1155_transfer_count: Optional[int] = Field(default=None)
