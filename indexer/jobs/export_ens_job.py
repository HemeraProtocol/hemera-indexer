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
from indexer.domain.block import Block
from indexer.domain.ens_model import ENSRegister
from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.hemera_ens import EnsHandler, CONTRACT_NAME_MAP
from indexer.specification.specification import (
    AlwaysFalseSpecification,
    AlwaysTrueSpecification,
    TransactionFilterByLogs, TopicSpecification,
)
from indexer.utils.reorg import set_reorg_sign

logger = logging.getLogger(__name__)


# Exports hemera_ens related info
class ExportEnsJob(FilterTransactionDataJob):
    dependency_types = [Transaction, Log]
    output_types = [ENSRegister]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._filters = kwargs.get("filters", [])
        self.ens_handler = EnsHandler()

        self._is_filter = all(output_type.is_filter_data() for output_type in self._required_output_types)
        self._specification = AlwaysFalseSpecification() if self._is_filter else AlwaysTrueSpecification()

    def get_filter(self):
        topics = []
        addresses = list(CONTRACT_NAME_MAP.keys())

        # topics.append(MESSAGE_DELIVERED_EVENT_SIG)
        # topics.append(INBOX_MESSAGE_DELIVERED_EVENT_SIG)
        # topics.append(BRIDGE_CALL_TRIGGERED_EVENT_SIG)
        # topics.append(NODE_CREATED_EVENT_SIG)
        # topics.append(NODE_CONFIRMED_EVENT_SIG)
        # topics.append(SEQUENCER_BATCH_DELIVERED_EVENT_SIG)

        return TransactionFilterByLogs([TopicSpecification(addresses=addresses, topics=topics)])

    def _start(self, **kwargs):
        if self.able_to_reorg and self._reorg:
            if self._service is None:
                raise FastShutdownError("PG Service is not set")

            reorg_block = int(kwargs["start_block"])
            set_reorg_sign(reorg_block, self._service)
            self._should_reorg_type.add(Block.type())
            self._should_reorg = True

    def _end(self):
        super()._end()
        self._specification = AlwaysFalseSpecification() if self._is_filter else AlwaysTrueSpecification()

    def _collect(self, **kwargs):
        transactions: List[Transaction] = self._data_buff.get(Transaction.type(), [])
        logs = self._data_buff.get(Log.type(), [])
        transactions_map = {ta["hash"]: ta for ta in transactions}
        items = []
        group_data = defaultdict(list)
        for dl in logs:
            group_data[dl['transaction_hash']].append(dl)
        for tnx, tnx_lgs in group_data.items():
            tra = transactions_map.get(tnx)
            dic_lis = self.ens_handler.process(tra, tnx_lgs)
            if dic_lis:
                items.extend(dic_lis)
        pass

    def _process(self, **kwargs):
        # TODO
        pass
