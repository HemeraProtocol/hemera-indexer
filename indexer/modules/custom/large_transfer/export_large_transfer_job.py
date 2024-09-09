#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/27 11:26
# @Author  will
# @File  export_ens_job.py
# @Brief
import logging
from collections import defaultdict
from typing import List

from common.utils.exception_control import FastShutdownError
from indexer.domain.token_transfer import ERC20TokenTransfer
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs.base_job import ExtensionJob
from indexer.modules.custom.large_transfer.domain.large_transfer_domain import LargeTransferD

logger = logging.getLogger(__name__)


class LargeTransferJob(ExtensionJob):
    dependency_types = [Transaction, ERC20TokenTransfer]
    output_types = [LargeTransferD]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self.limit_eth = self.user_defined_config.get("eth")

        self.rules = self.user_defined_config.get("rules")

        if self.limit_eth is None or len(self.rules) == 0:
            raise FastShutdownError("LargeTransferJob limit config is empty")

        self._is_batch = kwargs["batch_size"] > 1
        self._filters = kwargs.get("filters", [])

    def _collect(self, **kwargs):
        transactions: List[Transaction] = self._data_buff.get(Transaction.type(), [])
        token_transfers = self._data_buff.get(ERC20TokenTransfer.type(), [])
        transactions_map = {}
        group_data = defaultdict(list)
        for ta in transactions:
            transactions_map[ta.hash] = ta
            group_data[ta.hash] = []
        for tf in token_transfers:
            group_data[tf.transaction_hash].append(tf)

        res = []
        for tnx, tfs in group_data.items():
            tra = transactions_map.get(tnx)
            if tra.value > self.limit_eth:
                res.append(LargeTransferD(
                    transaction_hash=tra.hash,
                    transaction_index=tra.transaction_index,
                    from_address=tra.from_address,
                    to_address=tra.to_address,
                    value=tra.value,
                    transaction_type=tra.transaction_type,
                    input=tra.input,
                    method_id=tra.input,
                    nonce=tra.nonce,
                    block_hash=tra.block_hash,
                    block_number=tra.block_number,
                    block_timestamp=tra.block_timestamp,

                ))
            else:
                large_flag = False
                for tf in tfs:
                    for rule in self.rules:
                        if tf.token_address == rule["token_address"] and tf.value > rule["limit"]:
                            large_flag = True
                            break
                    if large_flag:
                        break
                if large_flag:
                    res.append(LargeTransferD(
                    transaction_hash=tra.hash,
                    transaction_index=tra.transaction_index,
                    from_address=tra.from_address,
                    to_address=tra.to_address,
                    value=tra.value,
                    transaction_type=tra.transaction_type,
                    input=tra.input,
                    method_id=tra.input,
                    nonce=tra.nonce,
                    block_hash=tra.block_hash,
                    block_number=tra.block_number,
                    block_timestamp=tra.block_timestamp,
                    ))

        for item in res:
            if item:
                self._collect_item(item.type(), item)
