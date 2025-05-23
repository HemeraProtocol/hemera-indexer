import logging
from itertools import groupby
from typing import List

from hemera.indexer.domains.log import Log
from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.executors.batch_work_executor import BatchWorkExecutor
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera_udf.cyber_id.abi.event import AddressChangedEvent, CyberEvent, NameChangedEvent, RegisterEvent
from hemera_udf.cyber_id.abi.function import CyberFunction, SetNameForAddrFunction, SetNameFunction
from hemera_udf.cyber_id.domains import *

logger = logging.getLogger(__name__)


class ExportCyberIDJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [CyberAddressD, CyberIDRegisterD, CyberAddressChangedD]
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
        self.contract_object_map = {}
        self.functions = {
            SetNameFunction.get_signature(): SetNameFunction,
            SetNameForAddrFunction.get_signature(): SetNameForAddrFunction,
        }
        self.events = {
            RegisterEvent.get_signature(): RegisterEvent,
            AddressChangedEvent.get_signature(): AddressChangedEvent,
        }

    def get_filter(self):
        return [
            TransactionFilterByLogs(
                [
                    TopicSpecification(
                        addresses=[
                            self.user_defined_config["cyber_id_public_resolver_contract_address"],
                            self.user_defined_config["cyber_id_token_contract_address"],
                        ],
                        topics=[NameChangedEvent.get_signature(), RegisterEvent.get_signature()],
                    )
                ]
            ),
        ]

    def _collect(self, **kwargs):
        pass

    def _process(self, **kwargs):
        transactions: List[Transaction] = self._data_buff.get(Transaction.type(), [])
        for transaction in transactions:
            self._process_transaction(transaction)

        logs: List[Log] = self._data_buff.get(Log.type(), [])
        for log in logs:
            self._process_log(log)

        # sort and deduplicate cyber addresses to avoid duplicate records
        cyber_addresses = self._data_buff.get(CyberAddressD.type(), [])
        cyber_addresses.sort(key=lambda x: (x.address, x.block_number))
        self._data_buff[CyberAddressD.type()] = [
            list(group)[-1] for key, group in groupby(cyber_addresses, key=lambda x: x.address)
        ]

        address_changes = self._data_buff.get(CyberAddressChangedD.type(), [])
        address_changes.sort(key=lambda x: (x.node, x.block_number))
        self._data_buff[CyberAddressChangedD.type()] = [
            list(group)[-1] for key, group in groupby(address_changes, key=lambda x: x.node)
        ]

    def _process_transaction(self, transaction: Transaction):
        function: CyberFunction = self.functions.get(transaction.input[0:10])
        if not function:
            return
        datas = function.process(transaction, **self.user_defined_config)
        if not datas:
            return
        for data in datas:
            self._collect_item(data.type(), data)

    def _process_log(self, log: Log):
        event: CyberEvent = self.events.get(log.topic0)
        if not event:
            return
        datas = event.process(log, **self.user_defined_config)
        if not datas:
            return
        for data in datas:
            self._collect_item(data.type(), data)
