#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/27 11:26
# @Author  will
# @File  export_ens_job.py
# @Brief
import logging
from collections import defaultdict
from typing import List

from sqlalchemy import and_

from common.utils.exception_control import FastShutdownError
from indexer.domain.token_transfer import ERC20TokenTransfer
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import ExtensionJob
from indexer.modules.custom.large_transfer.domain.large_transfer_domain import (
    LargeTransferAddressD,
    LargeTransferTransactionD,
)
from indexer.modules.custom.large_transfer.models.large_transfer_address import LargeTransferAddress

logger = logging.getLogger(__name__)

ETH = "0x0000000000000000000000000000000000000000"
TC = "transaction_count"


class LargeTransferJob(ExtensionJob):
    dependency_types = [Transaction, ERC20TokenTransfer]
    output_types = [LargeTransferAddressD, LargeTransferTransactionD]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self.limit_eth = self.get_eth_limit(self.user_defined_config)
        self.rules = self.user_defined_config.get("rules")
        self.validate_config()

        self._is_batch = kwargs["batch_size"] > 1
        self._filters = kwargs.get("filters", [])
        self.db_service = kwargs["config"].get("db_service")

    @staticmethod
    def get_eth_limit(config):
        return config.get("eth", 0) * (10**18)

    def validate_config(self):
        if self.limit_eth is None or not self.rules:
            raise FastShutdownError("LargeTransferJob limit config is empty")

    def _collect(self, **kwargs):
        transactions: List[Transaction] = self._data_buff.get(Transaction.type(), [])
        token_transfers = self._data_buff.get(ERC20TokenTransfer.type(), [])

        results, address_token_in, address_token_out = self.process(transactions, token_transfers)
        block_number = max(tx.block_number for tx in transactions)
        updated_transfers = self.update_large_transfers(address_token_in, address_token_out, block_number)
        for item in results + updated_transfers:
            if item:
                self._collect_item(item.type(), item)

    def process(self, transactions, token_transfers):
        transactions_map = {tx.hash: tx for tx in transactions}
        group_data = self.group_transfers_by_transaction(token_transfers)

        results = []
        address_token_in = defaultdict(lambda: defaultdict(int))
        address_token_out = defaultdict(lambda: defaultdict(int))

        for tx_hash, transfers in group_data.items():
            tx = transactions_map.get(tx_hash)
            if not tx:
                continue

            if self.is_large_eth_transfer(tx):
                results.append(self.create_large_transfer_transaction(tx))
                self.update_address_balances(address_token_in, address_token_out, tx, ETH)
            elif self.is_large_token_transfer(transfers):
                results.append(self.create_large_transfer_transaction(tx))
                self.update_token_balances(address_token_in, address_token_out, transfers)

        return results, address_token_in, address_token_out

    @staticmethod
    def group_transfers_by_transaction(token_transfers):
        group_data = defaultdict(list)
        for tf in token_transfers:
            group_data[tf.transaction_hash].append(tf)
        return group_data

    def is_large_eth_transfer(self, tx):
        return tx.value > self.limit_eth

    def is_large_token_transfer(self, transfers):
        return any(
            tf.value > (rule["limit"] * 10**6)
            for tf in transfers
            for rule in self.rules
            if tf.token_address == rule["token_address"]
        )

    @staticmethod
    def create_large_transfer_transaction(tx):
        return LargeTransferTransactionD(
            transaction_hash=tx.hash,
            transaction_index=tx.transaction_index,
            from_address=tx.from_address,
            to_address=tx.to_address,
            value=tx.value,
            transaction_type=tx.transaction_type,
            input=tx.input,
            nonce=tx.nonce,
            block_hash=tx.block_hash,
            block_number=tx.block_number,
            block_timestamp=tx.block_timestamp,
        )

    @staticmethod
    def update_address_balances(address_token_in, address_token_out, tx, token):
        address_token_in[tx.to_address][token] += tx.value
        address_token_in[tx.to_address][TC] += 1
        address_token_out[tx.from_address][token] += tx.value
        address_token_out[tx.from_address][TC] += 1

    def update_token_balances(self, address_token_in, address_token_out, transfers):
        for tf in transfers:
            for rule in self.rules:
                if tf.token_address == rule["token_address"] and tf.value > (rule["limit"] * 10**6):
                    self.update_address_balances(address_token_in, address_token_out, tf, tf.token_address)
                    break

    def get_existing_large_transfers(self, addresses, tokens):
        if not self.db_service:
            return {}

        addresses = [addr.encode("utf-8") if isinstance(addr, str) else addr for addr in addresses]
        tokens = [tok_addr.encode("utf-8") if isinstance(tok_addr, str) else tok_addr for tok_addr in tokens]
        with self.db_service.get_service_session() as session:
            result = (
                session.query(LargeTransferAddress)
                .filter(
                    and_(
                        LargeTransferAddress.address.in_(addresses),
                        LargeTransferAddress.token_address.in_(tokens),
                    )
                )
                .all()
            )

        return {
            f"{row.address}.{row.token_address}": LargeTransferAddressD(
                address=row.address,
                token_address=row.token_address,
                transaction_count=row.transaction_count,
                amount_in=row.amount_in,
                amount_out=row.amount_out,
                block_number=row.block_number,
            )
            for row in result
        }

    def update_large_transfers(self, address_token_in, address_token_out, block_number):
        addresses = set(address_token_in.keys()) | set(address_token_out.keys())
        tokens = set(self.get_second_level_keys(address_token_in)) | set(self.get_second_level_keys(address_token_out))

        existing_transfers = self.get_existing_large_transfers(addresses, tokens)

        for address, token_balance in address_token_in.items():
            self.update_transfer_record(existing_transfers, address, token_balance, block_number, is_inbound=True)

        for address, token_balance in address_token_out.items():
            self.update_transfer_record(existing_transfers, address, token_balance, block_number, is_inbound=False)

        return list(existing_transfers.values())

    @staticmethod
    def update_transfer_record(existing_transfers, address, token_balance, block_number, is_inbound):
        for token, balance in token_balance.items():
            key = f"{address}.{token}"
            if key in existing_transfers:
                record = existing_transfers[key]
                record.transaction_count += balance if token == TC else 1
                if token != TC:
                    if is_inbound:
                        record.amount_in += balance
                    else:
                        record.amount_out += balance
            elif token != TC:
                existing_transfers[key] = LargeTransferAddressD(
                    address=address,
                    token_address=token,
                    transaction_count=1,
                    amount_in=balance if is_inbound else 0,
                    amount_out=balance if not is_inbound else 0,
                    block_number=block_number,
                )

    @staticmethod
    def get_second_level_keys(nested_dict):
        return {key for subdict in nested_dict.values() for key in subdict}
