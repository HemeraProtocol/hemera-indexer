#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/24 下午6:05
Author  : xuzh
Project : hemera_indexer
"""
from typing import List

from common.models.blocks import Blocks
from common.models.transactions import Transactions
from common.utils.format_utils import bytes_to_hex_str


def validate_transaction_builder(transactions: List[Transactions]) -> List[str]:
    validate_transactions = []
    for transaction in transactions:
        validate_transactions.append(
            {
                "hash": bytes_to_hex_str(transaction.hash),
                "transaction_index": transaction.transaction_index,
                "from_address": bytes_to_hex_str(transaction.from_address),
                "to_address": bytes_to_hex_str(transaction.to_address),
                "value": int(transaction.value),
                "input": bytes_to_hex_str(transaction.input),
            }
        )

    return validate_transactions


def validate_block_builder(block: Blocks, transactions: List[Transactions]) -> dict:
    transactions = validate_transaction_builder(transactions)
    validate_block = {
        "hash": bytes_to_hex_str(block.hash),
        "number": block.number,
        "timestamp": block.timestamp.timestamp(),
        "parent_hash": bytes_to_hex_str(block.parent_hash),
        "transactions_count": block.transactions_count,
        "transactions": transactions,
        "extra_data": bytes_to_hex_str(block.extra_data),
    }
    return validate_block