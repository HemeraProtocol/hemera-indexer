#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/9/9 16:16
# @Author  will
# @File  large_transfer_domain.py
# @Brief
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from indexer.domain import Domain


@dataclass
class LargeTransferTransactionD(Domain):
    transaction_hash: str
    transaction_index: Optional[int] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    value: Optional[float] = None
    transaction_type: Optional[int] = None
    input: Optional[str] = None
    nonce: Optional[int] = None

    block_hash: Optional[str] = None
    block_number: Optional[int] = None
    block_timestamp: Optional[int] = None

    gas: Optional[float] = None
    gas_price: Optional[float] = None
    max_fee_per_gas: Optional[float] = None
    max_priority_fee_per_gas: Optional[float] = None

    exist_error: Optional[bool] = None
    error: Optional[str] = None
    revert_reason: Optional[str] = None

    reorg: Optional[bool] = False


@dataclass
class LargeTransferAddressD(Domain):
    address: str
    token_address: str
    transaction_count: int
    amount_in: int
    amount_out: int
    block_number: int
