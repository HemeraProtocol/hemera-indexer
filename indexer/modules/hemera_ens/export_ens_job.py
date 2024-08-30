#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/27 11:26
# @Author  will
# @File  export_ens_job.py
# @Brief
import logging
from collections import defaultdict
from dataclasses import asdict, is_dataclass, fields
from typing import List, Dict, Any

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.hemera_ens import CONTRACT_NAME_MAP, EnsConfLoader, EnsHandler
from indexer.modules.hemera_ens.ens_domain import ENSRegisterD, ENSMiddleD, ENSRegisterTokenD, ENSNameRenewD, \
    ENSAddressChangeD, ENSAddressD
from indexer.specification.specification import (
    AlwaysFalseSpecification,
    AlwaysTrueSpecification,
    TopicSpecification,
    TransactionFilterByLogs,
)

logger = logging.getLogger(__name__)


# Exports hemera_ens related info
class ExportEnsJob(FilterTransactionDataJob):
    dependency_types = [Transaction, Log]
    output_types = [ENSMiddleD, ENSRegisterD, ENSRegisterTokenD, ENSNameRenewD, ENSAddressChangeD, ENSAddressD]
    able_to_reorg = True

    def __init__(self, **kwargs):
        # TODO check chainId, only available on ethMainNet
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._filters = kwargs.get("filters", [])
        self.ens_handler = EnsHandler(EnsConfLoader())

        self._is_filter = all(output_type.is_filter_data() for output_type in self._required_output_types)
        self._specification = AlwaysFalseSpecification() if self._is_filter else AlwaysTrueSpecification()

    def get_filter(self):
        topics = []
        addresses = list(CONTRACT_NAME_MAP.keys())
        return TransactionFilterByLogs([TopicSpecification(addresses=addresses, topics=topics)])

    def _collect(self, **kwargs):
        transactions: List[Transaction] = self._data_buff.get(Transaction.type(), [])
        logs = self._data_buff.get(Log.type(), [])
        transactions_map = {ta.hash: asdict(ta) for ta in transactions}
        middles = []
        group_data = defaultdict(list)
        for dl in logs:
            group_data[dl.transaction_hash].append(asdict(dl))
        for tnx, tnx_lgs in group_data.items():
            tra = transactions_map.get(tnx)
            dic_lis = self.ens_handler.process(tra, tnx_lgs)
            if dic_lis:
                middles.extend(dic_lis)
        middles.sort(key=lambda x: (x.block_number, x.transaction_index, x.log_index), reverse=False)
        res = self.ens_handler.process_middle(middles)
        res = merge_ens_objects(res)
        for item in middles + res:
            if item:
                self._collect_item(item.type(), item)


def merge_ens_objects(objects: List[Any]) -> List[Any]:
    latest_objects: Dict[tuple, Any] = {}

    for obj in objects:
        if not is_dataclass(obj):
            continue

        key = (type(obj), getattr(obj, 'node', None))

        if key in latest_objects:
            for field in fields(obj):
                if getattr(obj, field.name) is not None:
                    setattr(latest_objects[key], field.name, getattr(obj, field.name))
        else:
            latest_objects[key] = obj

    return list(latest_objects.values())
