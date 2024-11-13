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
from indexer.domain import DomainMeta


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


def report_record_builder(records: List[dict]) -> List[dict]:
    formated_records = []
    merged_record_status = {}
    for record in records:

        report_details = []
        for detail in record.report_details:
            dataclass = DomainMeta._hash_mapping[detail["dataClass"]]
            report_details.append(
                {
                    "dataclass": dataclass,
                    "count": detail["count"],
                    "data_hash": "0x" + detail["dataHash"],
                }
            )

        transaction_hash = bytes_to_hex_str(record.transaction_hash)
        validate_status = record.status if record.status else "unverified"

        if transaction_hash in merged_record_status:
            formated_record = merged_record_status[transaction_hash]
            if validate_status != formated_record["validate_status"]:
                if validate_status == "Pass" or formated_record["validate_status"] == "pass":
                    formated_record["validate_status"] = "partially pass"
                else:
                    formated_record["validate_status"] = "failed"

        else:
            merged_record_status[transaction_hash] = {
                "chain_id": record.chain_id,
                "mission_type": record.mission_type,
                "start_block_number": record.start_block_number,
                "end_block_number": record.end_block_number,
                "runtime_code_hash": bytes_to_hex_str(record.runtime_code_hash),
                "report_details": report_details,
                "transaction_hash": bytes_to_hex_str(record.transaction_hash),
                "report_status": record.report_status.value,
                "validate_status": validate_status,
                "exception": record.exception,
                "report_time": int(record.create_time.timestamp()),
            }

    for transaction_hash in merged_record_status.keys():
        formated_records.append(merged_record_status[transaction_hash])

    formated_records.sort(key=lambda x: x["report_time"], reverse=True)

    return formated_records
